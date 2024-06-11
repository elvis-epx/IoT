#ifndef __MQTT_H
#define __MQTT_H

#include "MQTTBase.h"

class UptimePub: public PubTopic
{
public:
    UptimePub();
    virtual const char *value_gen() override;
};

class VolUnitPub: public PubTopic
{
public:
    VolUnitPub();
    virtual const char *value_gen() override;
};

class CoarseLevelPctPub: public PubTopic
{
public:
    CoarseLevelPctPub();
    virtual const char *value_gen() override;
};

class CoarseLevelVolPub: public PubTopic
{
public:
    CoarseLevelVolPub();
    virtual const char *value_gen() override;
};

class EstimatedLevelVolPub: public PubTopic
{
public:
    EstimatedLevelVolPub();
    virtual const char *value_gen() override;
};

class EstimatedLevelStrPub: public PubTopic
{
public:
    EstimatedLevelStrPub();
    virtual const char *value_gen() override;
};

class PumpedAfterLevelChangePub: public PubTopic
{
public:
    PumpedAfterLevelChangePub();
    virtual const char *value_gen() override;
};

class LevelErrPub: public PubTopic
{
public:
    LevelErrPub();
    virtual const char *value_gen() override;
};

class FlowPub: public PubTopic
{
public:
    FlowPub();
    virtual const char *value_gen() override;
};

class MQTT: public MQTTBase {
public:
    MQTT();

    const char *mqtt_id() const;
    const char *logdebug_topic() const;
    const char *ota_topic() const;
};

#endif
