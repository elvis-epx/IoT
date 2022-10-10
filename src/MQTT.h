#ifndef __MQTT_H
#define __MQTT_H

#include "MQTTBase.h"

class UptimePub: public PubTopic
{
public:
    UptimePub();
    virtual const char *value_gen() override;
};

class StatePub: public PubTopic
{
public:
    StatePub();
    virtual const char *value_gen() override;
};

class Level1Pub: public PubTopic
{
public:
    Level1Pub();
    virtual const char *value_gen() override;
};

class Level2Pub: public PubTopic
{
public:
    Level2Pub();
    virtual const char *value_gen() override;
};

class LevelErrPub: public PubTopic
{
public:
    LevelErrPub();
    virtual const char *value_gen() override;
};

class FlowInstPub: public PubTopic
{
public:
    FlowInstPub();
    virtual const char *value_gen() override;
};

class FlowShortPub: public PubTopic
{
public:
    FlowShortPub();
    virtual const char *value_gen() override;
};

class FlowLongPub: public PubTopic
{
public:
    FlowLongPub();
    virtual const char *value_gen() override;
};

class EfficiencyPub: public PubTopic
{
public:
    EfficiencyPub();
    virtual const char *value_gen() override;
};

class OverrideSub: public SubTopic
{
public:
    OverrideSub();
    int parse(const StrBuf&) const;
};

class OverrideOnSub: public OverrideSub
{
public:
    OverrideOnSub();
    virtual void new_value(const StrBuf&);
};

class OverrideOffSub: public OverrideSub 
{
public:
    OverrideOffSub();
    virtual void new_value(const StrBuf&);
};

class OverrideOnPub: public PubTopic
{
public:
    OverrideOnPub();
    virtual const char *value_gen() override;
};

class OverrideOffPub: public PubTopic
{
public:
    OverrideOffPub();
    virtual const char *value_gen() override;
};

class MQTT: public MQTTBase {
public:
    MQTT();
    bool override_on_state() const;
    bool override_off_state() const;
    void annotate_override_on_state(bool);
    void annotate_override_off_state(bool);

    const char *mqtt_id() const;
    const char *logdebug_topic() const;
    const char *ota_topic() const;

private:
    bool _override_on_state;
    bool _override_off_state;
};

#endif
