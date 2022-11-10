#ifndef __MQTT_H
#define __MQTT_H

#include "MQTTBase.h"

class UptimePub: public PubTopic
{
public:
    UptimePub();
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
