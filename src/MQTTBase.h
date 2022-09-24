#ifndef __MQTTBASE_H
#define __MQTTBASE_H

#include "Timestamp.h"
#include "Vector.h"
#include "Pointer.h"

class TopicName {
public:
    TopicName();
    TopicName(const char *);
    TopicName(const TopicName &);
    TopicName& operator=(TopicName const &);
    virtual ~TopicName();
    const char *c_str() const;
    bool equals(const TopicName&) const;
    bool equals(const char *) const;
private:
    char *_data;
};

class TopicValue {
public:
    TopicValue();
    TopicValue(const TopicValue &) = delete;
    TopicValue& operator=(TopicValue const &) = delete;
    virtual ~TopicValue();
    const char *c_str() const;
    void update(const char *);
    bool equals(const char *) const;
private:
    char *_data;
};

class PubTopic {
public:
    PubTopic();
    PubTopic(const PubTopic &) = delete;
    PubTopic& operator=(PubTopic const &) = delete;
    virtual ~PubTopic();
    TopicName topic() const;
    Ptr<TopicValue> value();
    virtual bool value_changed() = 0;
protected:
    TopicName _topic;
    Ptr<TopicValue> _value;
};

class SubTopic {
public:
    SubTopic();
    SubTopic(const SubTopic &) = delete;
    SubTopic& operator=(SubTopic const &) = delete;
    virtual ~SubTopic();
    TopicName topic() const;
    virtual void new_value(const char *, size_t) = 0;
protected:
    TopicName _topic;
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
    const char *wifi_status();
    const char *mqtt_status();

private:
    Ptr<PubTopic> pub_by_topic(const TopicName&);
    void republish_all();
	void sub_data_event(const char *topic, const char *payload, unsigned int length);
	void update_pub_data();
	void pub_data();
	void do_pub_data(const char *topic, const char *value) const;
	void init_mqttimpl();
	void chk_mqttimpl();
	void chk_wifi();
	void eval_mqttimpl();

	Timestamp last_wifi_check;
    bool wifi_connection_logged;
	Timestamp last_mqtt_check;
    Vector<TopicName> pub_pending;
	Timestamp last_pub_update;
	Timestamp last_general_pub;

protected:
    Vector<Ptr<PubTopic>> pub_topics;
    Vector<Ptr<SubTopic>> sub_topics;

friend void mqttimpl_trampoline2(const char* topic, const uint8_t* payload, unsigned int length);
};

void mqttimpl_trampoline2(const char* topic, const uint8_t* payload, unsigned int length);

#endif
