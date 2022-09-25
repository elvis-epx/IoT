#ifndef __MQTT_H
#define __MQTT_H

#include "MQTTBase.h"

#define PUB_UPTIME "stat/H2OControl/Uptime"
#define PUB_STATE "stat/H2OControl/State"
#define PUB_LEVEL1 "stat/H2OControl/Level1"
#define PUB_LEVEL2 "stat/H2OControl/Level2"
#define PUB_LEVELERR "stat/H2OControl/LevelErr"
#define PUB_FLOWINST "stat/H2OControl/FLowInst"
#define PUB_FLOWSHORT "stat/H2OControl/FlowShort"
#define PUB_FLOWLONG "stat/H2OControl/FlowLong"
#define PUB_EFFICIENCY "stat/H2OControl/Efficiency"
#define PUB_OVERRIDEON "stat/H2OControl/OverrideOn"
#define PUB_OVERRIDEOFF "stat/H2OControl/OverrideOff"

#define SUB_OVERRIDEON "cmnd/H2OControl/OverrideOn"
#define SUB_OVERRIDEOFF "cmnd/H2OControl/OverrideOff"

#define PUB_LOGDEBUG_TOPIC "tele/H2OControl/logdebug"
#define MQTT_RELAY_ID "H2OControl"

class UptimePub: public PubTopic
{
public:
    UptimePub();
    virtual bool value_changed();
};

class StatePub: public PubTopic
{
public:
    StatePub();
    virtual bool value_changed();
};

class Level1Pub: public PubTopic
{
public:
    Level1Pub();
    virtual bool value_changed();
};

class Level2Pub: public PubTopic
{
public:
    Level2Pub();
    virtual bool value_changed();
};

class LevelErrPub: public PubTopic
{
public:
    LevelErrPub();
    virtual bool value_changed();
};

class FlowInstPub: public PubTopic
{
public:
    FlowInstPub();
    virtual bool value_changed();
};

class FlowShortPub: public PubTopic
{
public:
    FlowShortPub();
    virtual bool value_changed();
};

class FlowLongPub: public PubTopic
{
public:
    FlowLongPub();
    virtual bool value_changed();
};

class EfficiencyPub: public PubTopic
{
public:
    EfficiencyPub();
    virtual bool value_changed();
};

class OverrideOnSub: public SubTopic
{
public:
    OverrideOnSub();
    virtual void new_value(const char *, size_t);
};

class OverrideOffSub: public SubTopic
{
public:
    OverrideOffSub();
    virtual void new_value(const char *, size_t);
};

class OverrideOnPub: public PubTopic
{
public:
    OverrideOnPub();
    virtual bool value_changed();
};

class OverrideOffPub: public PubTopic
{
public:
    OverrideOffPub();
    virtual bool value_changed();
};

class MQTT: public MQTTBase {
public:
    MQTT();
    void eval();
    bool override_on_state() const;
    bool override_off_state() const;
    void annotate_override_on_state(bool);
    void annotate_override_off_state(bool);

    const char *mqtt_id() const;
    const char *logdebug_topic() const;

private:
    bool _override_on_state;
    bool _override_off_state;
};

#endif
