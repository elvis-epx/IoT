#include <stdio.h>
#include "MQTT.h"
#include "Elements.h"
#include "Constants.h"
#include "LogDebug.h"

UptimePub::UptimePub()
{
    _topic = PUB_UPTIME;
}

VolUnitPub::VolUnitPub()
{
    _topic = PUB_VOLUME_UNIT;
}

CoarseLevelPctPub::CoarseLevelPctPub()
{
    _topic = PUB_COARSELEVEL_PCT;
}

CoarseLevelVolPub::CoarseLevelVolPub()
{
    _topic = PUB_COARSELEVEL_VOL;
}

PumpedAfterLevelChangePub::PumpedAfterLevelChangePub()
{
    _topic = PUB_PUMPEDAFTERLEVELCHANGE;
}

EstimatedLevelVolPub::EstimatedLevelVolPub()
{
    _topic = PUB_ESTIMATEDLEVEL_VOL;
}

EstimatedLevelStrPub::EstimatedLevelStrPub()
{
    _topic = PUB_ESTIMATEDLEVEL_STR;
}

LevelErrPub::LevelErrPub()
{
    _topic = PUB_LEVELERR;
}

FlowPub::FlowPub()
{
    _topic = PUB_FLOW;
}

const char *UptimePub::value_gen()
{
    Timestmp Now = now();
    static char tmp[30];
    sprintf(tmp, "%" PRId64, Now / (1 * MINUTES));
    return tmp;
}

const char *VolUnitPub::value_gen()
{
    static char tmp[10];
    sprintf(tmp, VOL_UNIT);
    return tmp;
}

const char *CoarseLevelPctPub::value_gen()
{
    static char tmp[30];
    sprintf(tmp, "%.0f", levelmeter->level_pct());
    return tmp;
}

const char *CoarseLevelVolPub::value_gen()
{
    static char tmp[30];
    sprintf(tmp, "%.0f", levelmeter->level_vol());
    return tmp;
}

const char *PumpedAfterLevelChangePub::value_gen()
{
    static char tmp[30];
    sprintf(tmp, "%.0f", flowmeter->volume());
    return tmp;
}

const char *EstimatedLevelVolPub::value_gen()
{
    static char tmp[30];
    sprintf(tmp, "%.0f", levelmeter->level_vol() + flowmeter->volume());
    return tmp;
}

const char *EstimatedLevelStrPub::value_gen()
{
    static char tmp[30];
    const char *err = levelmeter->failure_detected() ? "E " : "";
    sprintf(tmp, "%s%.0f%% + %.0f" VOL_UNIT, err, levelmeter->level_pct(), flowmeter->volume());
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
    pub_topics.push_back(Ptr<PubTopic>(new VolUnitPub()));
    pub_topics.push_back(Ptr<PubTopic>(new CoarseLevelVolPub()));
    pub_topics.push_back(Ptr<PubTopic>(new CoarseLevelPctPub()));
    pub_topics.push_back(Ptr<PubTopic>(new PumpedAfterLevelChangePub()));
    pub_topics.push_back(Ptr<PubTopic>(new EstimatedLevelVolPub()));
    pub_topics.push_back(Ptr<PubTopic>(new EstimatedLevelStrPub()));
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
