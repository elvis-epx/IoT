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
