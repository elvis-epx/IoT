#include <stdio.h>
#include "MQTT.h"
#include "Elements.h"
#include "Constants.h"
#include "LogDebug.h"

UptimePub::UptimePub()
{
    _topic = PUB_UPTIME;
}

Level1Pub::Level1Pub()
{
    _topic = PUB_LEVEL1;
}

Level2Pub::Level2Pub()
{
    _topic = PUB_LEVEL2;
}

LevelErrPub::LevelErrPub()
{
    _topic = PUB_LEVELERR;
}

FlowPub::FlowPub()
{
    _topic = PUB_FLOWINST;
}

const char *UptimePub::value_gen()
{
    Timestmp Now = now();
    static char tmp[30];
    sprintf(tmp, "%" PRId64, Now / (1 * MINUTES));
    return tmp;
}

const char *Level1Pub::value_gen()
{
    static char tmp[30];
    sprintf(tmp, "%.0f", levelmeter->level_pct());
    return tmp;
}

const char *Level2Pub::value_gen()
{
    static char tmp[30];
    sprintf(tmp, "%.0f", flowmeter->volume());
    return tmp;
}

const char *LevelErrPub::value_gen()
{
    return levelmeter->failure_detected() ? "1" : "0";
}

const char *FlowPub::value_gen()
{
    static char tmp[30];
    sprintf(tmp, "%.1f", flowmeter->rate());
    return tmp;
}

MQTT::MQTT()
{
    pub_topics.push_back(Ptr<PubTopic>(new UptimePub()));
    pub_topics.push_back(Ptr<PubTopic>(new Level1Pub()));
    pub_topics.push_back(Ptr<PubTopic>(new Level2Pub()));
    pub_topics.push_back(Ptr<PubTopic>(new LevelErrPub()));
    pub_topics.push_back(Ptr<PubTopic>(new FlowPub()));
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
    return MQTT_RELAY_ID;
}
