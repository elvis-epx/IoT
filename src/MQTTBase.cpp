#include "MQTTBase.h"
#include "LogDebug.h"
#include "Elements.h"
#include "NVRAM.h"

#ifdef UNDER_TEST

#include <iostream>
#include <fstream>

#else

#ifdef ESP8266
#include <ESP8266WiFi.h>
#else
#include <WiFi.h>
#endif

#include <PubSubClient.h>

WiFiClient wifi;
PubSubClient mqttimpl(wifi);

#endif

TopicName::TopicName()
{
    _data = strdup("");
}

TopicValue::TopicValue()
{
    _data = strdup("Undefined");
}

TopicName::TopicName(const char *s)
{
    _data = strdup(s);
}

TopicName::~TopicName()
{
    free(_data);
    _data = 0;
}

TopicName::TopicName(const TopicName &other)
{
    _data = strdup(other._data);
}

TopicName& TopicName::operator=(TopicName const &other)
{
    if (this != &other) {
        free(_data);
        _data = strdup(other._data);
    }
    return *this;
}

TopicValue::~TopicValue()
{
    free(_data);
    _data = 0;
}

const char *TopicName::c_str() const
{
    return _data;
}

const char *TopicValue::c_str() const
{
    return _data;
}

bool TopicName::equals(const TopicName& other) const 
{
    return equals(other.c_str());
}

bool TopicName::equals(const char *s) const
{
    return strcmp(_data, s) == 0;
}

bool TopicValue::equals(const char *s) const
{
    return strcmp(_data, s) == 0;
}

void TopicValue::update(const char *s)
{
    free(_data);
    _data = strdup(s);
}

// topic is set by subclass constructor
PubTopic::PubTopic()
{
    _value = Ptr<TopicValue>(new TopicValue());
}

SubTopic::SubTopic() {}

TopicName PubTopic::topic() const
{
    return _topic;
}

TopicName SubTopic::topic() const
{
    return _topic;
}

Ptr<TopicValue> PubTopic::value()
{
    return _value;
}

PubTopic::~PubTopic() {}
SubTopic::~SubTopic() {}

MQTTBase::MQTTBase()
{
    last_pub_update = now() - (1 * MINUTES);
    // first full republish is automatic because of MQTT init and/or
    // because data sources update pub values from Undefined to proper value
    last_general_pub = now();
    last_mqtt_check = now() - (30 * SECONDS);
    last_wifi_check = now() - (60 * SECONDS);
    wifi_connection_logged = false;

    wifi_ssid = arduino_nvram_load("ssid");
    wifi_password = arduino_nvram_load("password");
    mqtt_address = arduino_nvram_load("mqtt");
    char *mqtt_port_s = arduino_nvram_load("mqttport");
    if (strcmp(mqtt_port_s, "None") == 0) {
        mqtt_port = 1883;
    } else {
        mqtt_port = atoi(mqtt_port_s);
    }
    free(mqtt_port_s);
    wifi_enabled = strcmp(wifi_ssid, "None") != 0;
    mqtt_enabled = wifi_enabled && strcmp(mqtt_address, "None") != 0;
}

void MQTTBase::start()
{
    if (wifi_enabled) {
        Log::d("Wi-Fi configured");
        if (mqtt_enabled) {
            Log::d("MQTT configured");
        } else {
            Log::d("MQTT not configured");
        }
    } else {
        Log::d("Wi-Fi not configured");
    }
    init_mqttimpl();
}

void MQTTBase::republish_all()
{
    for(size_t i = 0; i < pub_topics.count(); ++i) {
        pub_pending.push_back(pub_topics[i]->topic());
    }
}

void mqttimpl_trampoline2(const char* topic, const uint8_t* bpayload, unsigned int length)
{
    char *payload = (char*) malloc(length + 1);
    memcpy(payload, bpayload, length);
    payload[length] = 0;
    mqtt->sub_data_event(topic, payload, length);
    free(payload);
}

#ifndef UNDER_TEST
void mqttimpl_trampoline(char* topic, uint8_t* bpayload, unsigned int length)
{
    mqttimpl_trampoline2(topic, bpayload, length);
}
#endif

void MQTTBase::init_mqttimpl()
{
#ifndef UNDER_TEST
    if (mqtt_enabled) {
        mqttimpl.setServer(mqtt_address, mqtt_port);
        mqttimpl.setCallback(mqttimpl_trampoline);
    }
#endif
}

const char *MQTTBase::mqtt_status()
{
    static char tmp[31];
#ifndef UNDER_TEST
    if (mqtt_enabled) {
        if (mqttimpl.connected()) {
            sprintf(tmp, "conn");
        } else {
            sprintf(tmp, "disconn %d", mqttimpl.state());
        }
    } else {
        sprintf(tmp, "dis");
    }
#else
    sprintf(tmp, "mock conn");
#endif
    return tmp;
}

void MQTTBase::chk_mqttimpl()
{
    Timestamp Now = now();
    if ((Now - last_mqtt_check) < (1 * MINUTES)) {
        return;
    }
    last_mqtt_check = Now;

#ifndef UNDER_TEST
    if (mqtt_enabled) {
        if (!mqttimpl.connected()) {
            Log::d("Connecting MQTT");
            if (mqttimpl.connect(mqtt_id())) {
                Log::d("MQTT connection up");
                for (size_t i = 0; i < sub_topics.count(); ++i) {
                    mqttimpl.subscribe(sub_topics[i]->topic().c_str());
                }
                // force full republish
                last_general_pub = 0;
            } else {
                Log::d("MQTT connection failed");
                Log::d("MQTT state", mqttimpl.state());
            }
        }
    }
#endif
}

void MQTTBase::eval_mqttimpl()
{
#ifndef UNDER_TEST
    if (mqtt_enabled) {
        mqttimpl.loop();
    }
#endif
}

const char *MQTTBase::wifi_status()
{
    static char tmp[31];
#ifndef UNDER_TEST
    if (wifi_enabled) {
        if (WiFi.status() == WL_CONNECTED) {
            sprintf(tmp, "%s", WiFi.localIP().toString().c_str());
        } else {
            sprintf(tmp, "disconn");
        }
    } else {
        sprintf(tmp, "dis");
    }
#else
    sprintf(tmp, "connected");
#endif
    return tmp;
}

void MQTTBase::chk_wifi()
{
    Timestamp Now = now();
    if ((Now - last_wifi_check) < (1 * MINUTES)) {
        return;
    }
    last_wifi_check = Now;

#ifndef UNDER_TEST
    if (wifi_enabled) {
        if (WiFi.status() == WL_CONNECTED) {
            if (!wifi_connection_logged) {
                Log::d("WiFi up, IP is ", WiFi.localIP().toString().c_str());
                wifi_connection_logged = true;
            }
            return;
        }
        wifi_connection_logged = false;
        Log::d("Connecting to WiFi...");
        if (strcmp(wifi_password, "None") == 0) {
            WiFi.begin(wifi_ssid);
        } else {
            WiFi.begin(wifi_ssid, wifi_password);
        }
    }
#endif
}

MQTTBase::~MQTTBase()
{
    free(wifi_ssid);
    free(wifi_password);
    free(mqtt_address);
}

void MQTTBase::sub_data_event(const char *topic, const char *payload, unsigned int length)
{
    for (size_t i = 0; i < sub_topics.count(); ++i) {
        Ptr<SubTopic> sub = sub_topics[i];
        if (! sub->topic().equals(topic)) {
            continue;
        }
        sub->new_value(payload, length);
        return;
    }
    Log::d("MQTT sub_data_event: unknown topic", topic);
}

void MQTTBase::eval()
{
    chk_wifi();
    chk_mqttimpl();
    eval_mqttimpl();

    update_pub_data();
    pub_data();
}

void MQTTBase::update_pub_data()
{
    Timestamp Now = now();
    if ((Now - last_pub_update) < 1000) {
        return;
    }
    last_pub_update = Now;

    for (size_t i = 0; i < pub_topics.count(); ++i) {
        Ptr<PubTopic> pub = pub_topics[i];
        if (pub->value_changed()) {
            pub_pending.push_back(pub->topic());
        }
    }
}

void MQTTBase::pub_data()
{
    Timestamp Now = now();
    if (((Now - last_general_pub) >= (30 * MINUTES))) {
        republish_all();
        last_general_pub = Now;
    }

    if (pub_pending.count() <= 0) {
        return;
    }
        
    // Do a single MQTT publish per cycle
    Ptr<PubTopic> pub = pub_by_topic(pub_pending[0]);
    pub_pending.remov(0);
    if (pub) {
        do_pub_data(pub->topic().c_str(), pub->value()->c_str());
    }
}

void MQTTBase::do_pub_data(const char *topic, const char *value) const
{
    // do not call Log::d() here to avoid infinite loop via pub_logdebug()
#ifdef UNDER_TEST
    std::ofstream f;
    f.open("mqttpub.sim", std::ios_base::app);
    f << topic << " " << value << std::endl;
    f.close();
#else
    if (mqtt_enabled) {
        mqttimpl.publish(topic, (const uint8_t*) value, strlen(value), true);
    }
#endif
}

void MQTTBase::pub_logdebug(const char *msg)
{
    // do not call Log::d() here to avoid infinite loop
    do_pub_data(logdebug_topic(), msg);
}

Ptr<PubTopic> MQTTBase::pub_by_topic(const TopicName& name)
{
    for (size_t i = 0; i < pub_topics.count(); ++i) {
        if (pub_topics[i]->topic().equals(name)) {
            return pub_topics[i];
        }
    }
    return Ptr<PubTopic>(0);
}
