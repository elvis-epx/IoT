# MicroPython automation projects

This is a personal project for home automation written in MicroPython. At the moment,
it has no intention of becoming the next Tasmota or ESPHome. It is directed to the
devices I have, documentation is lacking and it is not very configurable.

Nevertheless, it is written and maintained to be very reliable, so it could be useful
as reference for people starting at MicroPython, or trying to interface with some
device similar to those we use. I plan to add more documentation for every module
as possible.

We adopt the ESP32 as default MCU for our projects, so we currently are not concerned
with broad compatibility with other chips, though we try to keep machine-level things
abstract.

## General structure

The project has basically two parts: the common modules, and the profile-specific
modules. A profile is an incarnation of an automation appliance. e.g. water tank
level (h2o), home lightning control (switch), mains energy meter (energy) and so on.

## Anatomy of a profile

Taking the energy profile as an example, a profile is composed of the following files,
at the minimum:

- energy\_boot.py that becomes the boot.py when installed into the ESP32
- energy\_main.py that becomes the main.py
- energy\_config.txt.example is an example of configuration file for the profile
- energy\_config.txt is the configuration file (based on the example above) that you should create for your particular need. This becomes the file config.txt in the ESP32. The pcp\_conf script automates the copy of this file to the MCU.
- energy.mpf is a manifest used by the cpall script (based on mpfshell) to upload all code to the ESP32 via serialA

The following files are optional, but generally they exist:

- energy.ota is a manifest that directs the OTA update of the code (otascript tool).
- energy\_stage.py is used by testing and coverage framework.
- lib/energy/\*.py are the profile-specific modules

The profile-specific modules tend to follow a pattern:

- lib/profile/sensor.py contains interfaces with hardware sensors. Some modules talk directly with the hardware, some do it through third-party modules found at lib/third/.
- lib/profile/actuator.py contains interfaces with hardware actuators.
- lib/profile/service.py contains classes that represent MQTT topics (published and subscribed).

## Anatomy of the common modules

The following files are included in in basically every profile's manifest:

- lib/epx/loop.py: implements basic elements like the event loop, state machine, and other bits and pieces.
- lib/epx/config.py: deals with the configuration file config.txt
- lib/epx/watchdog.py: implements a watchdog, very necessary for reliability (software may freeze, MCUs may freeze as well).
- lib/epx/net.py: handles the network (WiFi and LAN). Interfaces with native network APIs. There are many provisions to ensure the network communication is reliable, including resetting the MCU when the network keeps failing (the radio may go comatose, which is rare but does happen, and a good automation appliance must recover from that).
- lib/epx/mqtt.py: handles the MQTT messaging and supplies interfaces for easy interaction with MQTT. Uses the uumqtt module. Also has provisions to ensure reliability, including resetting the MCU when MQTT can't be reached for too long.
- lib/epx/ota.py: implements an OTA scheme, as well as some remote debugging resources.
- lib/epx/nvram.py: interface to NVRAM for persistent data storage.
- lib/uumqtt/\*.py: modified version of the umqtt module, with some improvements related to blocking and exception handling in order to make the whole system more reliable. Using our own MQTT library allows us not to be affected by breaking changes in the umqtt bundled with MicroPython image.

Each profile may also add any number of files from lib/third/ folder. These modules are third-party modules,
generally device drivers, that are included in the source code for convenience. We generally tweak these
modules to make them more reliable and for them to fit better in our event-loop-based framework.

The lib/epx/netnow.py module interfaces with ESP-NOW and is used only by the profiles that employ ESP-NOW
(currently, only the "scale" profile).

## The event loop

The core of our framework is the event loop. It implements an asynchronous programming model analog to
Node.js or a select()-based UNIX program. The watchdog is integrated with the main loop and triggers 
on any excessive delay (e.g. infinite loop or long sleep).

This means your code should never block for too long. It should not busy-loop nor call time.sleep() by
itself to delay some operation. It should always schedule using a Task() or a state machine, unless it is
a very time-sensitive and rather fast operation like bitbanging a 74LS595 or a PS/2 keyboard. The watchdog
timeout is generous (15s) but blocking for too long would slow down MQTT handling, etc.

Blocking APIs should be avoided. Nonblocking APIs + polling or IRQs should be used instead.
If there is some underlying API that blocks and can't be fixed (e.g. socket.connect()), 
the problematic section must be surrounded by watchdog.may\_block() and watchdog.may\_block\_exit().
In the interim, the watchdog will be fed by a secondary thread (so it still catches hardware freezes).

Since the network traffic of the typical automation appliance is very light, it is currently handled by
polling. We may use asyncio in the future, and some hardware interfacing could use IRQs.
(Currently we only use IRQs to count pulses from a flow meter in h2o profile.)

The event loop does call time.sleep() when idle, but this won't put the ESP32 MCU to sleep. MicroPython
currently does not use the "automatic light sleep" feature available in ESP-IDF, but it may use it in the
future, and then our framework will enable significant energy savings.

Still about energy, we use the profile\_boot.py to set the MCU frequency. In all our profiles, we 
set it to 80Mhz, which allows the ESP32 to run cooler and we don't see the need of more performance.

## ESP-NOW protocol

Given the peculiarities of the ESP-NOW protocol, we implement a simple but minimally secure application
protocol that can be found in lib/epx/netnow.py, and is currently used by the scale profiles 
(scale\_sensor and scale\_manager).

The NetNowPeripheral class is for peripheral devices that only use ESP-NOW, not the regular Wi-Fi.
The communicate only with their paired manager/forwarder, and generally take the initiative of
communication. These devices may sleep to save power.

The NetNowCentral class is for central devices that use both ESP-NOW and regular Wi-Fi, and can forward
data between the two realms. These devices are expected to stay on all the time.

In ESP-NOW, you need to register a peer to sent data to that peer, and the number of registered peers
is limited. On the other hand, you can receive from anyone, as long as you don't use the ESP-NOW 
cryptography.

Given this quirk, in our implementation the peripheral device registers the central device as a peer
and sends packets directly to it, while the central device only sends broadcast packets (even if it is
actually addressing a particular peripheral). This elides the peer count limit.

### Wi-Fi channels

Since the ESP-NOW does not need an access point, the peers must agree somehow on the Wi-Fi channel
to use.

In our implementation, the ESP-NOW of the central device passively uses the channel set by regular
Wi-Fi (which can be set in config.txt, or will be the channel configured at the nearest access point).

The peripheral device stores the channel in NVRAM when it pairs with a central device. In unpaired state,
it keeps changing channels to find the central.

### Group and password

Each central and peripheral device has two config tokens: espnowpsk (pre-shared password or PSK) and
espnowgroup (device group). Only devices that share the same two values can communicate to each other.
On the other hand, many groups can share the air without conflict.

The PSK is used to calculate HMAC for every packet. Only packets with valid HMACs are processed.
The HMAC ensures the packet was generated by some peer that knows the PSK.

Currently, the PSK is not used to encrypt the payloads.

### Replay attacks from peripherals

Replay attacks are repelled by the central based on two tokens of information present in every packet:
timestamp and transaction ID (tid).

The timestamp is maintained and broadcast by the central and starts with a random value.
Legit peripherals send packets with the latest timestamp. The central accepts slightly outdated
timestamps just in case the peripheral has missed the last broadcast.

A new timestamp is broadcast by the central at least twice per minute, plus every time a packet is
confirmed.

The timestamp deflects replay attacks that reuse packets older than 2 or 3 minutes.

The transaction ID (tid) is a random nonce attached to every packet, both from central and
peripherals. In the current implementation, the central caches the tids received in the last
few minutes, and drops packets with repeated tids.

The tid deflects replay attacks that try to reuse fresh packets (seen in the last 2 or 3 minutes,
whose timestamps are still considered valid).

TODO: when the peripheral starts up, it needs to receive the timestamp first, to be able then to
send data. This does not work well for peripherals that a) sleep and b) are expected to send data
as fast as possible e.g. a coin cell remote control. Some other mechanism must be implemented to
accomodate this use case.

### Replay attacks from attackers posing as a central

The peripheral only accepts timestamps that are reasonable increments from the previously
known timestamp.

If an unexpected timestamp arrives, a ping packet is sent to the central, using
the new putative timestamp. Only the central can send a valid confirmation since the
ping packet has a unique TID, and the central won't confirm a ping with an invalid
timestamp.

Once the confirmation arrives, the rebased timestamp is accepted.

### Pairing

There is no special protocol for pairing. It is based on coincidence of PSK and group.

The only provision for pairing is a special "pair request" packet the peripheral sends
blind to broadcast. When a central device sees this packet, it updates the timestamp early,
which sends a timestamp packet that is hopefully detected by the peripheral.

At peripheral side, the peer central is stored in NVRAM. The presence of this data means the
device is paired. This data should be removed from NVRAM in order to put the device in unpaired
mode. Currently, this can be done by creating a file "pair.txt" in the ESP32 filesystem. 
A profile can add other methods e.g. pressing a button.

When unpaired, the peripheral actively scans for a suitable central peer, changing the Wi-Fi
channel every 5 seconds, sending pair req packets, and listening for timestamp broadcasts.
The profile may set a timeout (e.g. 5 minutes) to quit and go back to sleep.

Once the peripheral gets a valid timestamp packet, it adopts the central that sent it as its
manager. It simply stores the MAC address and the channel in NVRAM.

While it is possible to pair w/o activating the pairing mode in central, it will take a long
time, possibly exceeding some timeout set by the profile.
