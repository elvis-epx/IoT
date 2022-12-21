#include <stdlib.h>
#ifdef ESP8266
#include <ESP8266WiFi.h>
#else
#include <WiFi.h>
#endif
#ifndef UNDER_TEST
#include <ArduinoOTA.h>
#endif
#if defined(ESP32)
#include <esp_task_wdt.h>
#endif

#include <PubSubClient.h>

#include "MQTTBase.h"
#include "LogDebug.h"
#include "Elements.h"
#include "Constants.h"
#include "NVRAM.h"
#include "Console.h"

WiFiClient wifi;
PubSubClient mqttimpl(wifi);

// topic is set by subclass constructor
PubTopic::PubTopic()
{
}

SubTopic::SubTopic() {}

StrBuf PubTopic::topic() const
{
    return _topic;
}

StrBuf SubTopic::topic() const
{
    return _topic;
}

StrBuf* PubTopic::value()
{
    return &_value;
}

// override if necessary
bool PubTopic::retained()
{
    return false;
}

bool PubTopic::value_has_changed()
{
    const char *candidate = value_gen();
    if (value()->equals(candidate)) {
        return false;
    }
    value()->update(candidate);
    return true;
}

OTATopic::OTATopic(const char *topic)
{
    _topic = topic;
}

void OTATopic::new_value(const StrBuf& v)
{
    if (! v.equals(OTA_PASSWORD)) return;
    mqtt->activate_ota();
}

PubTopic::~PubTopic() {}
SubTopic::~SubTopic() {}

MQTTBase::MQTTBase()
{
    // first full republish is automatic because of MQTT init and/or
    // because data sources update pub values from Undefined to proper value
    next_general_pub = Timeout(30 * MINUTES);
    next_pub_update = Timeout(1 * SECONDS);
    next_pub_update.advance();
    next_mqtt_check = Timeout(30 * SECONDS);
    next_wifi_check = Timeout(60 * SECONDS);
    next_wifi_check.advance();
    wifi_connection_logged = false;

    arduino_nvram_load(wifi_ssid, "ssid");
    arduino_nvram_load(wifi_password, "password");
    arduino_nvram_load(mqtt_address, "mqtt");
    StrBuf mqtt_port_s;
    arduino_nvram_load(mqtt_port_s,"mqttport");
    if (mqtt_port_s.equals("None")) {
        mqtt_port = 1883;
    } else {
        mqtt_port = atoi(mqtt_port_s.c_str());
    }
    wifi_enabled = !wifi_ssid.equals("None");
    mqtt_enabled = wifi_enabled && !mqtt_address.equals("None");

    ota_activated = false;
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

    const char *ota = ota_topic();
    if (ota) {
        auto ota_sub = Ptr<SubTopic>(new OTATopic(ota));
        sub_topics.push_back(ota_sub);
    }

    init_mqttimpl();
}

void MQTTBase::republish_all()
{
    for(size_t i = 0; i < pub_topics.count(); ++i) {
        pub_pending.push_back(pub_topics[i]->topic());
    }
}

static StrBuf sub_payload;

void mqttimpl_trampoline(const char* topic, const uint8_t* payload, unsigned int length)
{
    sub_payload.reserve(length);
    memcpy(sub_payload.hot_str(), payload, length);
    sub_payload.hot_str()[length] = 0;
    mqtt->sub_data_event(topic, sub_payload);
}

void MQTTBase::init_mqttimpl()
{
    if (mqtt_enabled) {
        mqttimpl.setServer(mqtt_address.c_str(), mqtt_port);
        mqttimpl.setCallback(mqttimpl_trampoline);
    }
}

const char *MQTTBase::mqtt_status()
{
    static char tmp[31];
    if (mqtt_enabled) {
        if (mqttimpl.connected()) {
            sprintf(tmp, "conn");
        } else {
            sprintf(tmp, "disconn %d", mqttimpl.state());
        }
    } else {
        sprintf(tmp, "dis");
    }
    return tmp;
}

void MQTTBase::chk_mqttimpl()
{
    if (next_mqtt_check.pending()) {
        return;
    }

    if (mqtt_enabled) {
        if (!mqttimpl.connected()) {
            Log::d("Connecting MQTT");
            if (mqttimpl.connect(mqtt_id())) {
                Log::d("MQTT connection up");
                for (size_t i = 0; i < sub_topics.count(); ++i) {
                    mqttimpl.subscribe(sub_topics[i]->topic().c_str());
                }
                // force full republish
                next_general_pub.advance();
            } else {
                Log::d("MQTT connection failed");
                Log::d("MQTT state", mqttimpl.state());
            }
        }
    }
}

void MQTTBase::eval_mqttimpl()
{
    if (mqtt_enabled) {
        mqttimpl.loop();
    }
    if (ota_activated) {
#ifndef UNDER_TEST
        ArduinoOTA.handle();
#endif
    }
}

const char *MQTTBase::wifi_status()
{
    static char tmp[31];
    if (wifi_enabled) {
        if (WiFi.status() == WL_CONNECTED) {
            sprintf(tmp, "%s", WiFi.localIP().toString().c_str());
        } else {
            sprintf(tmp, "disconn");
        }
    } else {
        sprintf(tmp, "dis");
    }
    return tmp;
}

void MQTTBase::chk_wifi()
{
    if (next_wifi_check.pending()) {
        return;
    }

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
        if (wifi_password.equals("None")) {
            WiFi.begin(wifi_ssid.c_str());
        } else {
            WiFi.begin(wifi_ssid.c_str(), wifi_password.c_str());
        }
    }
}

MQTTBase::~MQTTBase()
{
    pub_topics.clear();
    sub_topics.clear();
}

void MQTTBase::sub_data_event(const char *topic, const StrBuf &payload)
{
    for (size_t i = 0; i < sub_topics.count(); ++i) {
        Ptr<SubTopic> sub = sub_topics[i];
        if (! sub->topic().equals(topic)) {
            continue;
        }
        sub->new_value(payload);
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
    if (!next_pub_update.pending()) {
        return;
    }

    for (size_t i = 0; i < pub_topics.count(); ++i) {
        Ptr<PubTopic> pub = pub_topics[i];
        if (pub->value_has_changed()) {
            pub_pending.push_back(pub->topic());
        }
    }
}

void MQTTBase::pub_data()
{
    if (!next_general_pub.pending()) {
        republish_all();
    }

    if (pub_pending.count() <= 0) {
        return;
    }
        
    // Do a single MQTT publish per cycle
    Ptr<PubTopic> pub = pub_by_topic(pub_pending[0]);
    pub_pending.remov(0);
    if (pub) {
        do_pub_data(pub->topic().c_str(), pub->value()->c_str(), pub->retained());
    }
}

void MQTTBase::do_pub_data(const char *topic, const char *value, bool retained) const
{
    // do not call Log::d() here to avoid infinite loop via pub_logdebug()
    if (mqtt_enabled) {
        mqttimpl.publish(topic, (const uint8_t*) value, strlen(value), retained);
    }
}

void MQTTBase::pub_logdebug(const char *msg)
{
    // do not call Log::d() here to avoid infinite loop
    do_pub_data(logdebug_topic(), msg, false);
}

Ptr<PubTopic> MQTTBase::pub_by_topic(const StrBuf& name)
{
    for (size_t i = 0; i < pub_topics.count(); ++i) {
        if (pub_topics[i]->topic().equals(name)) {
            return pub_topics[i];
        }
    }
    return Ptr<PubTopic>(0);
}

void MQTTBase::activate_ota()
{
    if (ota_activated) return;

#ifndef UNDER_TEST
    ArduinoOTA.onStart([]() {
        console_println("OTA onStart");
    });
    ArduinoOTA.onEnd([]() {
        console_println("OTA onEnd");
    });
    ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
        console_println("OTA progress...");
    });
    ArduinoOTA.onError([](ota_error_t error) {
        if (error == OTA_AUTH_ERROR) {
            console_println("OTA authentication failure");
        } else if (error == OTA_BEGIN_ERROR) {
            console_println("OTA failure at begin");
        } else if (error == OTA_CONNECT_ERROR) {
            console_println("OTA connection failure");
        } else if (error == OTA_RECEIVE_ERROR) {
            console_println("OTA rx failure");
        } else if (error == OTA_END_ERROR) {
            console_println("OTA failure at end");
        } else {
            console_println("OTA unspecified error");
        }
    });
    ArduinoOTA.begin();
    // disable hardware watchdog because OTA causes long event loop blocks
#if defined(ESP32)
    esp_task_wdt_delete(NULL);
#endif
#ifdef ESP8266
    ESP.wdtEnable(500);
#endif
#endif
    console_println("OTA activated");
    ota_activated = true;
}
