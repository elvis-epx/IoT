#ifndef __CONSTANTS_H
#define __CONSTANTS_H

#define NVRAM_CHAPTER "TempSensor"

#define PUB_UPTIME "stat/TempSensor/Uptime"
#define PUB_TEMPERATURE "stat/TempSensor/Temperature"
#define PUB_HUMIDITY "stat/TempSensor/Humidity"
#define SUB_OTA_TOPIC "cmnd/TempSensor/OTA"
#define OTA_PASSWORD "abracadabra"
#define MQTT_ID "TempSensor"
#define PUB_LOGDEBUG_TOPIC "tele/TempSensor/logdebug"

#if defined(ESP32)

#define DHTPIN 4
#define DHTTYPE DHT11

#elif defined(UNDER_TEST)

#define DHTPIN 0
#define DHTTYPE 11

#else

#define DHTPIN D1
#define DHTTYPE DHT11

#endif

#endif
