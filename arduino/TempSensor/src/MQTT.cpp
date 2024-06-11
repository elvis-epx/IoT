#include <stdio.h>

#include "MQTT.h"
#include "Elements.h"
#include "Constants.h"
#include "LogDebug.h"

UptimePub::UptimePub()
{
    _topic = PUB_UPTIME;
}

const char *UptimePub::value_gen()
{
    Timestmp Now = now();
    gentmp.reserve(30);
    sprintf(gentmp.hot_str(), "%" PRId64, Now / (1 * MINUTES));
    return gentmp.c_str();
}

TemperaturePub::TemperaturePub()
{
    _topic = PUB_TEMPERATURE;
}

HumidityPub::HumidityPub()
{
    _topic = PUB_HUMIDITY;
}

const char *TemperaturePub::value_gen()
{
    gentmp.reserve(20);
    if (isnan(sensor->temperature())) {
        sprintf(gentmp.hot_str(), "--");
    } else {
        sprintf(gentmp.hot_str(), "%.1f", sensor->temperature());
    }
    return gentmp.c_str();
}

const char *HumidityPub::value_gen()
{
    gentmp.reserve(20);
    if (isnan(sensor->humidity())) {
        sprintf(gentmp.hot_str(), "--");
    } else {
        sprintf(gentmp.hot_str(), "%.1f", sensor->humidity());
    }
    return gentmp.c_str();
}

MQTT::MQTT()
{
    auto uptime = Ptr<PubTopic>(new UptimePub());
    pub_topics.push_back(uptime);
    auto t = Ptr<PubTopic>(new TemperaturePub());
    pub_topics.push_back(t);
    auto h = Ptr<PubTopic>(new HumidityPub());
    pub_topics.push_back(h);
}

const char *MQTT::logdebug_topic() const
{
    return PUB_LOGDEBUG_TOPIC;
}

const char *MQTT::ota_topic() const
{
    return SUB_OTA_TOPIC;
}

const char *MQTT::mqtt_id() const
{
    return MQTT_ID;
}
