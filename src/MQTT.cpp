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
    _topic = TopicName(PUB_UPTIME);
}

OverrideOnPub::OverrideOnPub()
{
    _topic = TopicName(PUB_OVERRIDEON);
}

OverrideOffPub::OverrideOffPub()
{
    _topic = TopicName(PUB_OVERRIDEOFF);
}

Level1Pub::Level1Pub()
{
    _topic = TopicName(PUB_LEVEL1);
}

Level2Pub::Level2Pub()
{
    _topic = TopicName(PUB_LEVEL2);
}

LevelErrPub::LevelErrPub()
{
    _topic = TopicName(PUB_LEVELERR);
}

FlowInstPub::FlowInstPub()
{
    _topic = TopicName(PUB_FLOWINST);
}

FlowShortPub::FlowShortPub()
{
    _topic = TopicName(PUB_FLOWSHORT);
}

FlowLongPub::FlowLongPub()
{
    _topic = TopicName(PUB_FLOWLONG);
}

StatePub::StatePub()
{
    _topic = TopicName(PUB_STATE);
}

EfficiencyPub::EfficiencyPub()
{
    _topic = TopicName(PUB_EFFICIENCY);
}

OverrideOnSub::OverrideOnSub()
{
    _topic = TopicName(SUB_OVERRIDEON);
}

OverrideOffSub::OverrideOffSub()
{
    _topic = TopicName(SUB_OVERRIDEOFF);
}

bool OverrideOnPub::value_changed()
{
    const char *tmp = mqtt->override_on_state() ? "1" : "0";
    if (value()->equals(tmp)) {
        return false;
    }
    value()->update(tmp);
    return true;
}

bool OverrideOffPub::value_changed()
{
    const char *tmp = mqtt->override_off_state() ? "1" : "0";
    if (value()->equals(tmp)) {
        return false;
    }
    value()->update(tmp);
    return true;
}

bool UptimePub::value_changed()
{
	Timestamp Now = now();
    char tmp[30];
    sprintf(tmp, "%lld", Now / (1 * MINUTES));
    if (value()->equals(tmp)) {
        return false;
    }
    value()->update(tmp);
    return true;
}

bool StatePub::value_changed()
{
    if (value()->equals(sm->cur_state_name())) {
        return false;
    }
    value()->update(sm->cur_state_name());
    return true;
}

void OverrideOnSub::new_value(const char *v, size_t s)
{
	if (strncasecmp(v, "On", s) == 0) {
        mqtt->annotate_override_on_state(true);
	} else if (strncasecmp(v, "1", s) == 0) {
        mqtt->annotate_override_on_state(true);
	} else if (strncasecmp(v, "Off", s) == 0) {
        mqtt->annotate_override_on_state(false);
	} else if (strncasecmp(v, "0", s) == 0) {
        mqtt->annotate_override_on_state(false);
	}
}

void OverrideOffSub::new_value(const char *v, size_t s)
{
	if (strncasecmp(v, "On", s) == 0) {
        mqtt->annotate_override_off_state(true);
	} else if (strncasecmp(v, "1", s) == 0) {
        mqtt->annotate_override_off_state(true);
	} else if (strncasecmp(v, "Off", s) == 0) {
        mqtt->annotate_override_off_state(false);
	} else if (strncasecmp(v, "0", s) == 0) {
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

void MQTT::eval()
{
    // must call super method
    MQTTBase::eval();
#ifdef UNDER_TEST
   // simulate receiving MQTT commands
   std::ifstream f;
   int x = 0;
   f.open("mqtt.sim");
   if (f.is_open()) {
       f >> x;
       std::remove("mqtt.sim");
   }
   f.close();
   if (x == 1) {
       mqttimpl_trampoline2(SUB_OVERRIDEON, (uint8_t*) ((random() % 2) ? "On" : "1"), 2);
   } else if (x == 2) {
       mqttimpl_trampoline2(SUB_OVERRIDEON, (uint8_t*) ((random() % 2) ? "Off" : "0"), 3);
   } else if (x == 3) {
       mqttimpl_trampoline2(SUB_OVERRIDEOFF, (uint8_t*) ((random() % 2) ? "on" : "1"), 2);
   } else if (x == 4) {
       mqttimpl_trampoline2(SUB_OVERRIDEOFF, (uint8_t*) ((random() % 2) ? "off" : "0"), 3);
   }
#endif
}

