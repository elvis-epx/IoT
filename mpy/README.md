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

So, to create a new profile, you would probably take the most similar profile that already exists, and copy all
these files using the new profile name as prefix.

## Anatomy of the common modules

The following files are included in in basically every profile's manifest:

- lib/epx: base modules
- lib/epx/loop.py: implements basic elements like the event loop, state machine, and other bits and pieces.
- lib/epx/config.py: deals with the configuration file config.txt
- lib/epx/watchdog.py: implements a watchdog
- lib/epx/net.py: handles the network (WiFi and LAN). Interfaces with native network APIs.
- lib/epx/mqtt.py: handles the MQTT messaging. Uses the uumqtt module
- lib/epx/ota.py: implements an OTA scheme, as well as some remote debugging resources.
- lib/epx/nvram.py: interface to NVRAM for persistent data storage.
- lib/uumqtt/\*.py: modified version of the umqtt module, with some improvements related to blocking and exception handling in order to make the whole system more reliable. Using our own MQTT library allows us not to be affected by breaking changes in the umqtt bundled with MicroPython image.

Each profile may also add any number of files from lib/third/ folder. These modules are third-party modules,
generally device drivers, that are included in the source code for convenience. We generally tweak these
modules to make them more reliable and for them to fit better in our event-loop-based framework.
