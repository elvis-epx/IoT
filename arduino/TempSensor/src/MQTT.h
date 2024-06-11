#ifndef __MQTT_H
#define __MQTT_H

#include "MQTTBase.h"

class UptimePub: public PubTopic
{
public:
    UptimePub();
    virtual const char *value_gen();
private:
    StrBuf gentmp;
};

class TemperaturePub: public PubTopic
{
public:
    TemperaturePub();
    virtual const char *value_gen();
private:
    StrBuf gentmp;
};

class HumidityPub: public PubTopic
{
public:
    HumidityPub();
    virtual const char *value_gen();
private:
    StrBuf gentmp;
};

class MQTT: public MQTTBase {
public:
    MQTT();

    const char *mqtt_id() const;
    const char *logdebug_topic() const;
    const char *ota_topic() const;
};

#endif
