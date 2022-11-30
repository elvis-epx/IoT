#ifndef __MQTTBASE_H
#define __MQTTBASE_H

#include <stdio.h>
#include "Timer.h"
#include "Vector.h"
#include "Pointer.h"
#include "StrBuf.h"

class PubTopic {
public:
    PubTopic();
    PubTopic(const PubTopic &) = delete;
    PubTopic& operator=(PubTopic const &) = delete;
    virtual ~PubTopic();
    StrBuf topic() const;
    StrBuf *value();
    virtual bool retained();
    virtual bool value_has_changed();
    virtual const char *value_gen() = 0;
protected:
    StrBuf _topic;
    StrBuf _value;
};

class SubTopic {
public:
    SubTopic();
    SubTopic(const SubTopic &) = delete;
    SubTopic& operator=(SubTopic const &) = delete;
    virtual ~SubTopic();
    StrBuf topic() const;
    virtual void new_value(const StrBuf&) = 0;
protected:
    StrBuf _topic;
};

class OTATopic: public SubTopic {
public:
    OTATopic(const char *);
    void new_value(const StrBuf&);
};

class MQTTBase {
public:
    MQTTBase();
    virtual ~MQTTBase();

    void start();
    void eval();
    void pub_logdebug(const char *);

    virtual const char *mqtt_id() const = 0;
    virtual const char *logdebug_topic() const = 0;
    virtual const char *ota_topic() const = 0;
    void activate_ota();
    const char *wifi_status();
    const char *mqtt_status();

    // made public for coverage
    Ptr<PubTopic> pub_by_topic(const StrBuf&);

private:
    void republish_all();
    void sub_data_event(const char *topic, const StrBuf &payload);
    void update_pub_data();
    void pub_data();
    void do_pub_data(const char *topic, const char *value, bool retained) const;
    void init_mqttimpl();
    void chk_mqttimpl();
    void chk_wifi();
    void eval_mqttimpl();

    bool wifi_enabled;
    bool mqtt_enabled;
    StrBuf wifi_ssid;
    StrBuf wifi_password;
    StrBuf mqtt_address;
    int mqtt_port;

    Timeout next_wifi_check;
    bool wifi_connection_logged;
    Timeout next_mqtt_check;
    Vector<StrBuf> pub_pending;
    Timeout next_pub_update;
    Timeout next_general_pub;

    bool ota_activated;

protected:
    Vector<Ptr<PubTopic>> pub_topics;
    Vector<Ptr<SubTopic>> sub_topics;

friend void mqttimpl_trampoline(const char* topic, const uint8_t* payload, unsigned int length);
};

#endif
