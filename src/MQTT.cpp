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

bool Level1Pub::value_changed()
{
    char tmp[30];
    sprintf(tmp, "%.0f", levelmeter->level_pct());
    if (value()->equals(tmp)) {
        return false;
    }
    value()->update(tmp);
    return true;
}

bool Level2Pub::value_changed()
{
    char tmp[30];
    sprintf(tmp, "%.0f", flowmeter->volume());
    if (value()->equals(tmp)) {
        return false;
    }
    value()->update(tmp);
    return true;
}

bool LevelErrPub::value_changed()
{
    const char *msg = levelmeter->failure_detected() ? "1" : "0";
    if (value()->equals(msg)) {
        return false;
    }
    value()->update(msg);
    return true;
}

bool FlowInstPub::value_changed()
{
    char tmp[30];
    if (flowmeter->rate(FLOWRATE_INSTANT) < 0) {
        sprintf(tmp, "0");
    } else {
        sprintf(tmp, "%.1f", flowmeter->rate(FLOWRATE_INSTANT));
    }
    if (value()->equals(tmp)) {
        return false;
    }
    value()->update(tmp);
    return true;
}

bool FlowShortPub::value_changed()
{
    char tmp[30];
    if (flowmeter->rate(FLOWRATE_SHORT) < 0) {
        sprintf(tmp, "0");
    } else {
        sprintf(tmp, "%.1f", flowmeter->rate(FLOWRATE_SHORT));
    }
    if (value()->equals(tmp)) {
        return false;
    }
    value()->update(tmp);
    return true;
}

bool FlowLongPub::value_changed()
{
    char tmp[30];
    if (flowmeter->rate(FLOWRATE_LONG) < 0) {
        sprintf(tmp, "0");
    } else {
        sprintf(tmp, "%.1f", flowmeter->rate(FLOWRATE_LONG));
    }
    if (value()->equals(tmp)) {
        return false;
    }
    value()->update(tmp);
    return true;
}

bool EfficiencyPub::value_changed()
{
    char tmp[30];
    if (pump->is_running()) {
        double volume = flowmeter->volume();
        double exp_volume = flowmeter->expected_volume() + 0.0001;
        sprintf(tmp, "%.0f", 100 * volume / exp_volume);
    } else {
        sprintf(tmp, "0");
    }
    if (value()->equals(tmp)) {
        return false;
    }
    value()->update(tmp);
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
   if (x <= 0) {
       return;
   }

   const char *sub_topic = "Invalid@#!";
   const char *msg = "Invalid@#!";
   static const char *msg_on_variants[] = {"On", "on", "1"};
   static const char *msg_off_variants[] = {"Off", "off", "0"};
   if (x == 1) {
       sub_topic = SUB_OVERRIDEON;
       msg = msg_on_variants[random() % 3];
   } else if (x == 2) {
       sub_topic = SUB_OVERRIDEON;
       msg = msg_off_variants[random() % 3];
   } else if (x == 3) {
       sub_topic = SUB_OVERRIDEOFF;
       msg = msg_on_variants[random() % 3];
   } else if (x == 4) {
       sub_topic = SUB_OVERRIDEOFF;
       msg = msg_off_variants[random() % 3];
   } else if (x == 5) {
       sub_topic = "NoSuchSubTopic";
       msg = msg_on_variants[random() % 3];
   } else if (x == 6) {
       sub_topic = SUB_OVERRIDEON;
       msg = "Invalid@#!";
   } else if (x == 7) {
       sub_topic = SUB_OVERRIDEOFF;
       msg = "Invalid@#!";
   }
   mqttimpl_trampoline2(sub_topic, (uint8_t*) msg, strlen(msg) + 1);
#endif
}

