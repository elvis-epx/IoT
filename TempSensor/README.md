# TempSensor - IoT controller

This is a very vanilla IoT project to read temperature from a DHT11 and
publish via MQTT.

## Image confguration

The file `src/Constants.h` specifies MQTT topics and GPIO pin connected to
the DHT sensor.

## Target hardware

Currently, ESP8266 (NodeMCU) and ESP32 are the main targets.

## Network configuration

Wi-Fi and MQTT broker are configured via serial console and saved in flash memory,
so there is no need to hardcode these values in the build image.

In serial console, send the `!help` command to see the available configurations, as well
as other assorted commands.

## MicroPython version

In `micropython/` source folder, there is a MicroPython version that does the same
as the C++ version.

The MicroPython version uses some third-party libraries, bundled as part of the
repository:

- a slightly modified version of the umqtt.simple2 library
(https://github.com/fizista/micropython-umqtt.simple2) included as a folder. It is
possible to use the bundle umqtt.simple library instead.

- a BME280 I2C driver written by Rui Santos (randomnerdtutorials.com), code can be
found at https://github.com/RuiSantosdotme/ESP-MicroPython/tree/master/code/WiFi/HTTP\_Client\_IFTTT\_BME280.

- an HDC1080 I2C driver from https://github.com/digidotcom/xbee-micropython/blob/master/lib/sensor/hdc1080/hdc1080.py
published by Digi.
