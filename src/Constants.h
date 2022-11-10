#ifndef __CONSTANTS_H
#define __CONSTANTS_H

#define VOL_UNIT "L"
#define TANK_CAPACITY 1000.0

#define LEVEL_SENSORS {20.0, 40.0, 60.0, 80.0, 100.0, 0.0}
#define LEVEL_SENSOR_MASK 0b11111;

#define FLOWMETER_PULSE_RATE 4.8 // in pulses/s when flow is 1 unit/min
#define FLOWMETER_PIN 14

#define RELAY_INVERSE_LOGIC true /* for 3V3 relay modules with inverse pin logic */
// FIXME move MyGPIO native pand MCP23017 pin config here

#define NVRAM_CHAPTER "H2OControl"

#define PUB_UPTIME "stat/H2OControl/Uptime"
#define PUB_LEVEL1 "stat/H2OControl/Level1"
#define PUB_LEVEL2 "stat/H2OControl/Level2"
#define PUB_LEVELERR "stat/H2OControl/LevelErr"
#define PUB_FLOWINST "stat/H2OControl/FLow"

#define PUB_LOGDEBUG_TOPIC "tele/H2OControl/logdebug"
#define SUB_OTA_TOPIC "cmnd/H2OControl/OTA"
#define OTA_PASSWORD "abracadabra"
#define MQTT_RELAY_ID "H2OControl"

#endif
