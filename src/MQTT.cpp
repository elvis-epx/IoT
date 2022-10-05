#include <stdio.h>

#ifdef UNDER_TEST

#include <iostream>
#include <fstream>

#endif

#include "MQTT.h"
#include "Elements.h"
#include "Constants.h"
#include "LogDebug.h"

UptimePub::UptimePub()
{
    _topic = PUB_UPTIME;
}

OverrideOnPub::OverrideOnPub()
{
    _topic = PUB_OVERRIDEON;
}

OverrideOffPub::OverrideOffPub()
{
    _topic = PUB_OVERRIDEOFF;
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

FlowInstPub::FlowInstPub()
{
    _topic = PUB_FLOWINST;
}

FlowShortPub::FlowShortPub()
{
    _topic = PUB_FLOWSHORT;
}

FlowLongPub::FlowLongPub()
{
    _topic = PUB_FLOWLONG;
}

StatePub::StatePub()
{
    _topic = PUB_STATE;
}

EfficiencyPub::EfficiencyPub()
{
    _topic = PUB_EFFICIENCY;
}

OverrideSub::OverrideSub() {}

OverrideOnSub::OverrideOnSub()
{
    _topic = SUB_OVERRIDEON;
}

OverrideOffSub::OverrideOffSub()
{
    _topic = SUB_OVERRIDEOFF;
}

const char *OverrideOnPub::value_gen()
{
    return mqtt->override_on_state() ? "1" : "0";
}

const char *OverrideOffPub::value_gen()
{
    return mqtt->override_off_state() ? "1" : "0";
}

const char *UptimePub::value_gen()
{
    Timestmp Now = now();
    static char tmp[30];
    sprintf(tmp, "%lld", Now / (1 * MINUTES));
    return tmp;
}

const char *StatePub::value_gen()
{
    return sm->cur_state_name();
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

const char *FlowInstPub::value_gen()
{
    static char tmp[30];
    if (flowmeter->rate(FLOWRATE_INSTANT) < 0) {
        sprintf(tmp, "0");
    } else {
        sprintf(tmp, "%.1f", flowmeter->rate(FLOWRATE_INSTANT));
    }
    return tmp;
}

const char *FlowShortPub::value_gen()
{
    static char tmp[30];
    if (flowmeter->rate(FLOWRATE_SHORT) < 0) {
        sprintf(tmp, "0");
    } else {
        sprintf(tmp, "%.1f", flowmeter->rate(FLOWRATE_SHORT));
    }
    return tmp;
}

const char *FlowLongPub::value_gen()
{
    static char tmp[30];
    if (flowmeter->rate(FLOWRATE_LONG) < 0) {
        sprintf(tmp, "0");
    } else {
        sprintf(tmp, "%.1f", flowmeter->rate(FLOWRATE_LONG));
    }
    return tmp;
}

const char *EfficiencyPub::value_gen()
{
    static char tmp[30];
    if (pump->is_running()) {
        double volume = flowmeter->volume();
        double exp_volume = flowmeter->expected_volume() + 0.0001;
        sprintf(tmp, "%.0f", 100 * volume / exp_volume);
    } else {
        sprintf(tmp, "0");
    }
    return tmp;
}

int OverrideSub::parse(const StrBuf &v) const
{
    if (v.equalsi("On") || v.equalsi("1")) {
        return 1;
    } else if (v.equalsi("Off") || v.equalsi("0")) {
        return -1;
    }
    return 0;
}

void OverrideOnSub::new_value(const StrBuf &v)
{
    int res = parse(v);
    
    if (res == 1) {
        mqtt->annotate_override_on_state(true);
    } else if (res == -1) {
        mqtt->annotate_override_on_state(false);
    }
}

void OverrideOffSub::new_value(const StrBuf &v)
{
    int res = parse(v);
    
    if (res == 1) {
        mqtt->annotate_override_off_state(true);
    } else if (res == -1) {
        mqtt->annotate_override_off_state(false);
    }
}

MQTT::MQTT()
{
    _override_on_state = false;
    _override_off_state = false;

    pub_topics.push_back(Ptr<PubTopic>(new UptimePub()));
    pub_topics.push_back(Ptr<PubTopic>(new StatePub()));
    pub_topics.push_back(Ptr<PubTopic>(new Level1Pub()));
    pub_topics.push_back(Ptr<PubTopic>(new Level2Pub()));
    pub_topics.push_back(Ptr<PubTopic>(new LevelErrPub()));
    pub_topics.push_back(Ptr<PubTopic>(new FlowInstPub()));
    pub_topics.push_back(Ptr<PubTopic>(new FlowShortPub()));
    pub_topics.push_back(Ptr<PubTopic>(new FlowLongPub()));
    pub_topics.push_back(Ptr<PubTopic>(new EfficiencyPub()));
    pub_topics.push_back(Ptr<PubTopic>(new OverrideOnPub()));
    pub_topics.push_back(Ptr<PubTopic>(new OverrideOffPub()));

    sub_topics.push_back(Ptr<SubTopic>(new OverrideOnSub()));
    sub_topics.push_back(Ptr<SubTopic>(new OverrideOffSub()));
}

const char *MQTT::logdebug_topic() const
{
    return PUB_LOGDEBUG_TOPIC;
}

const char *MQTT::mqtt_id() const
{
    return MQTT_RELAY_ID;
}

bool MQTT::override_on_state() const
{
    return _override_on_state;
}

void MQTT::annotate_override_on_state(bool state)
{
    _override_on_state = state;
}

bool MQTT::override_off_state() const
{
    return _override_off_state;
}

void MQTT::annotate_override_off_state(bool state)
{
    _override_off_state = state;
}
