# H2OControl - IoT water tank monitor

This is an IoT project to monitor a water tank and control a water pump.
It is designed to detect and handle some failure scenarios e.g. faulty
sensor or dry well. The controller can report status and accept commands
via MQTT.

Currently, the project is aimed to fulfill personal needs. In the future 
it may be improved to cover more use cases.

Working on breadboard:

![Original image](https://raw.githubusercontent.com/elvis-epx/H2OControl/main/doc/breadboard.jpeg)

First prototype, connected to a simulator of the various sensors. The flow meter pulse train is
simulated by an Arduino (separate source at folder pwm/). It is fed with 5V via sensor cable,
since the real flow sensor also needs 5V to work:

![Original image](https://raw.githubusercontent.com/elvis-epx/H2OControl/main/doc/proto.jpeg)

## Override on and off

Sometimes it is necessary to turn the pump on/off manually. The idea is
to have two plain switches at controller case, to cut off and to bypass
the relay respectively, so the local override is guaranteed to work, even if the 
controller is faulty.

![Original image](https://raw.githubusercontent.com/elvis-epx/H2OControl/main/doc/circuit1.jpeg)

It is also nice to be able to override the controller remotely, so there
are two logic override switches accessible via MQTT. This allows for integration
with home automation strategies e.g. force the pump off at certain days and hours.

## System model

The main system model constants are configured in src/Constants.h.
Some are self-explaining, we will add documentation about the others
as time permits (studying the code should clarify what they mean, anyway).

## Choice of sensors 

Currently, the target use case employs a number of switch level sensors,
installed at various levels of the tank. These sensors are cheaper and more
reliable than analog/continuous level sensors. The topmost sensor must be
at 100% level.

![Original image](https://raw.githubusercontent.com/elvis-epx/H2OControl/main/doc/circuit2.jpeg)

The PWM inflow sensor allows to detect proper water flow (or lack thereof).
The combination with level sensors allows to detect other failures e.g.
water leaks or flow rate too low.

We chose not to use an outflow sensor,
but this could be implemented to control the tank even better (e.g. avoid
false leak alarms,  detect if there is a leak in the water tank itself).

The inflow sensor is expected to be near the water tank, not near the
pump, so a second inflow sensor (or a simple on/off flow sensor) near
the pump could be added to detect a pump failure sooner. In current
implementation, the program waits enough time to fill the pipes between
pump and sensor.

Using 5 switch sensors plus the inflow sensor, we need a grand total of
8 wires, and an Ethernet cable is enough to connect the water tank to the
controller.

## Target hardware

Currently, ESP8266 (NodeMCU) and ESP32 are the main targets, we use either
in test modules. We use Arduino tools to compile and install the software.

The project expects the following peripherals: an SSD1306-based display,
an MCP23017 I/O multiplexer (level switches inputs + relay output), and a
PWM flow sensor connected directly to a GPIO pin.

Since most flow sensors are 5V, there must be a level shifter
(be it a resistor divider or a proper circuit) somewhere between the
sensor output and the MCU pin. The PWM signal goes directly to the MCU
so we can use interrupts to count the pulses.

## Testing

Great emphasis is made on testing and achieving high code coverage, since
debugging is generally difficult on MCUs (a little easier on ESP32, but
still).

Unit tests can be found at test/ and run on Linux or macOS. In Linux,
the tests run with Valgrind for additional assurance.
Sensors and actuators are mocked by the unit test scripts. Some Arduino APIs
e.g. millis() and random() are mocked as well.

Testing on actual platform needs some hardware setup to simulate sensors
and actuators. One can use a protoboard, or a separate case containing
switches, lights etc. that behave electrically the same as the real peripherals.

The pwm/ folder contains a small Arduino project that simulates the PWM
flow sensor, using a potentiometer to change the pulse frequency. 
We use an AVR Nano so the output is 5V, like the real flow sensor, so
we can be sure the level shifter is doing its job.

## Network configuration

Wi-Fi and MQTT broker are configured via serial console and saved in flash memory,
so there is no need to hardcode these values in the build image.

In serial console, send the `!help` command to see the available configurations, as well
as other assorted commands.
