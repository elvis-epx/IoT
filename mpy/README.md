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

- profiles/energy/boot.py that becomes the boot.py when installed into the ESP32
- profiles/energy/main.py that becomes the main.py
- profiles/energy/stage.py is used by testing and coverage framework.
- profiles/energy/config.txt.example is an example of configuration file for the profile
- profiles/energy/manifest.mpf is used by the cpall script (based on mpfshell) to upload all code to the ESP32 via serial port.
- profiles/energy/manifest.ota directs the OTA update of the code (otascript tool).

You should create a config file for your particular need. This becomes the file config.txt in the ESP32. The pcp\_conf script automates the copy of this file to the MCU.

The following files are optional, but generally they exist:

- lib/energy/\*.py are the profile-specific modules

Using now the h2o profile as example, the profile-specific modules tend to follow a pattern:

- lib/h2o/sensor.py contains interfaces to hardware sensors, if they exist. Some modules talk directly with the hardware, some do it through third-party modules found at lib/third/.
- lib/h2o/actuator.py contains interfaces with hardware actuators, if they exist.
- lib/h2o/service.py contains classes that represent MQTT topics (published and subscribed), or ESP-NOW topics.

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
modules to make them more reliable and to fit better in our event-loop-based framework.

The lib/epx/netnow.py module interfaces with ESP-NOW and is used only by the profiles that employ ESP-NOW
(currently, only the "scale" profile).

## CLI utilities

There are a number of primitive CLI tools available:

- pcp: copy a file via serial port using `mpfshell`
- pcp\_conf: copy a file that becomes /config.txt in the target
- pcp\_main: copy a file that becomes /main.py in the target
- cpall: copy all necessary files, driven by the profile manifest, except the config file

In order to use the tools above, first create a local file named `serial_params.txt` that contains
the mpfshell parameters related to serial port, something like `-o ttyUSB0` or `-o ttyUSB0 --reset`.

In general, we use `cpall <profile>` followed by `pcp_conf <my config file>` to first configure a
device, and then use OTA for further updates.

OTA tools:

- otatool: low-level tool to send a single file using the OTA network protocol, or retrieve the hash of an existing file.
- ota\_config: send one file via OTA that becomes /config.txt in the target
- otascript: send all changed files via OTA. Compares file hashes to send only the ones that have changed.
- otacmd: send command to topic `cmnd/$1/OTA`
- monmqtt: monitor the topic `stat/$1/Log`
- ota: high-level tool that uses `otascript`, discovers the IP address of the target, etc.

In general, we only use the `ota` tool to upgrade the MicroPython code and is the easiest to use.
In the rare occasion we need to update the config file, then we use `ota_config`. More about OTA
in a later section of this document.

In order to use `ota`, first create a local file named `mqttserver.txt` that contains the name or the
IP address of the MQTT broker, since we use MQTT to open OTA in the target device, and discover its
address.

OTA firmware tool:

- otafwtool: OTA tool to update the MicroPython interpreter. It is not completely autonomous, there are
a number of steps that are still responsibility of the user.

Test tools:

- entool: ESP-NOW protocol simulator
- runtest: runs a test script contained in testsuites/
- test.py: Python cradle that loads a profile in test mode, to run in a PC
- utest.py: same as test.py but for unit tests.

# OTA code upgrade and observability

The framework supports OTA update of any files, be it code, configuration, etc. The basic procedure to update one file is:

- Send message `open` to device topic `cmnd/DeviceName/OTA`, using `otacmd` or `mosquitto_pub` or by any other means. This will open a network socket.
- Use the `otatool` script to send the file using the OTA protocol. The file will get a temporary name.
- Send message `commit` to `cmnd/DeviceName/OTA`. This actually replaces the old file.
- Send message `reboot` to `cmnd/DeviceName/OTA`.

In order to use `otatool` you need to know the IP address of the device. After sending `open` to OTA, the IP address is
published via topic `stat/DeviceName/Log` to be discoverable via MQTT.

The `ota` script does all the steps above automatically.

IMPORTANT: the OTA code update does not currently support rollbacks, so make sure you have run the code in a test device
before shipping. Otherwise, if MicroPython fails, OTA will be unreachable as well, and you will have to resort to serial
port.

# OTA observability

Other commands accepted by `cmnd/DeviceName/OTA`:

- `stats`: produce network statistics
- `msg_reboot`: produce reason for the last reboot
- `msg_exception`: produce last exception backtrace
- `msg_rm`: clear the two messages above, works as "mark as read"

These commands report their output via `stat/DeviceName/Log`, and the device accepts them anytime, it is not necessary
to send the `open` command before.

# OTA firmware upgrade

The framework also implements a protocol for the OTA firmware upgrade. The OTA variant of the MicroPython firmware must
have been installed previously, so the flash memory has the proper layout to support this operation.

The current procedure is:

- Subscribe to `stat/DeviceName/Log` to get the output of the commands below. Use `mqttmon` script or `mosquitto_sub`.
- Optionally, send `getversion` to `cmnd/DeviceName/OTA` (using `otacmd` or `mosquitto_pub`) to check the version that is currently running.
- send `open` to `cmnd/DeviceName/OTA`.
- discover the IP address of the device (will be logged every 10 seconds or so).
- use the `otafwtool` to send the new firmware. Make sure to send only the Micropython binary (.app.bin) not the whole flashable image (.bin). If in doubt, remember that .app.bin is always the smaller of the two.
- send `reboot` to `cmnd/DeviceName/OTA` to run the new firmware

If the devices does not come up, just power cycle at this point, and it will revert to the old firmware. If the device does start:

- send `getversion` to `cmnd/DeviceName/OTA`, to make sure the device is actually running the new firmware version.
- Make sure the device is working properly, doing tests or having tested previously on a canary device.
- Finally, send `keepversion` to `cmnd/DeviceName/OTA` to commit the new firmware version.
- Optionally, `reboot` and `getversion` again to ensure the new firmware did stick.

The command `partitions` produces the number of firmware partitions and the current active partition. This is useful
to discover whether the firmware can receive OTA updates. If there are two partitions, it can. If there is a single one,
it cannot.

# Testing and coverage

The framework currently uses an ad-hoc scheme for E2E testing, unit testing and coverage report. It runs on
regular Python on a PC or Mac. (This means the framework code under test must be equally valid MicroPython and Python.)

The current test suite is not in the best shape, the E2E tests are time-dependent and sometimes they fail. It should
be improved in the future, but it currently does a fair job of exercising near 100% of the code.

The `testmock/` folder contains Python code to mock hardware drivers and/or or replace MicroPython-only modules.

The `testsuite/' folder contains the individual tests, each one in its own subfolder. Each test has a `config.txt`,
a `flavor` file identifying the profile, and a `script` that drives the test.

The `runtest` script runs individual tests. Running the whole test suite is driven by a `Makefile`. Do `make clean`
followed by `make test`. 

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

Since the network traffic of the typical automation appliance is very light, parts of the code handle
it by polling (i.e. checking every 100ms or so). At least MQTT and ESP-NOW handle incoming traffic the
"right" way i.e. using select.poll to wait on data. We may use asyncio in the future, and some hardware
interfacing could use IRQs. (Currently we only use IRQs to count pulses from a flow meter in h2o profile.)

The event loop does call time.sleep() or poll.poll() as it should in a UNIX environment, but this won't put the ESP32 MCU to sleep.
MicroPython currently does not use the "automatic light sleep" feature available in ESP-IDF, but it might use
it in the future, and then our framework will enable significant energy savings.

Still about energy, we use the profile\_boot.py to set the MCU frequency. In most profiles we 
set it to 80Mhz which allows the ESP32 to run cooler and we don't see the need of more performance.

## ESP-NOW protocol

Given the peculiarities of the ESP-NOW protocol, we implement a simple but minimally secure application
protocol that can be found in lib/epx/netnow.py, and is currently used by the scale profiles 
(scale\_sensor and scale\_manager).

The NetNowPeripheral class is for peripheral devices that only use ESP-NOW, not the regular Wi-Fi.
They communicate only with their paired manager/forwarder, and generally take the initiative of
communication. These devices may sleep to save power.

The NetNowCentral class is for central devices that use both ESP-NOW and regular Wi-Fi, and can forward
data between the two realms. These devices do not sleep.

In ESP-NOW, you need to register a peer to sent data to it, and the number of registered peers
is limited. On the other hand, you can receive from anyone, as long as you don't use the ESP-NOW 
cryptography.

Given this quirk, in our implementation the peripheral device registers the central device as a peer
and sends packets directly to it, while the central device only sends broadcast packets (even when
targeting a particular peripheral). This elides the peer count limit.

### Wi-Fi channels

Since the ESP-NOW network does not have an access point, the peers must agree somehow on which
Wi-Fi channel to use.

In our implementation, the ESP-NOW of the central device passively uses the channel set by regular
Wi-Fi. It follows the channel configured at the access point.

The peripheral device stores the channel in NVRAM when it pairs with a central device. In unpaired state,
it keeps changing channels to find the central.

### Group and password

Every central and peripheral device has two config tokens: espnowpsk (pre-shared password or PSK) and
espnowgroup (device group). Only devices that share the same two values can communicate to each other.
On the other hand, many groups can share the air without conflict, even if they use the same PSK.

Currently, the PSK is used to sign the HMAC and to encrypt the payload. The ideal mechanism would
be to use PSK to exchange new keys at pairing time.

### Replay attacks

Replay attacks are repelled by the central using the textbook approach of HMACs, timestamps
and unique random transaction IDs (tids). The central device maintains and broadcasts the "network
time".

The peripheral only accepts time updates that are reasonable increments from the
currently known time. If an unexpected time value arrives, a ping packet is
sent to the central to seek confirmation.

Similar to the ping packet, there is also the wakeup packet, sent when the peripheral
starts up or wakes up, so it does not have to wait until the next broadcast to learn
the network time (important for real-time use cases like remote controls).

Wakeup, ping and pair request packets are 3 different types because they are different
vectors for a DoS attack, and the strategy to throttle each type could be different.

### Pairing

There is no special protocol for pairing. It is based on coincidence of PSK and group.

The only provision for pairing is a special "pair request" packet the peripheral broadcasts
blindly. When a central device sees this packet, it broadcasts the network time
immediately to be seen by the peripheral.

At peripheral side, the central device is stored in NVRAM, as well as the Wi-Fi channel
in which the central device was found. To force a re-pair,
create a file "pair.txt" in the ESP32 filesystem. A profile can add other methods e.g.
pressing a button.

When unpaired, the peripheral actively scans for a suitable central peer, changing the Wi-Fi
channel often and broadcasting pair requests. The profile may set a timeout (e.g. 5 minutes)
to quit and go back to sleep.
