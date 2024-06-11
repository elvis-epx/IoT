#include <stdio.h>
#include <string.h>
#include <iostream>
#include <fstream>
#include "PubSubClient.h"

PubSubClient::PubSubClient(WiFiClient& ap)
{
    _state = -1;
    _invalid = true;
    callback = 0;
}

int PubSubClient::state()
{
    return _state;
}

void PubSubClient::loop()
{
    if (! connected()) return;
    std::ifstream f;
    f.open("mqtt.sim");
    if (f.is_open()) {
        char topic[80];
        char value[80];
        char ok[80];
        f.getline(topic, 80);
        f.getline(value, 80);
        f.getline(ok, 80);
        if (strcmp(ok, "Ok") == 0) {
            printf("MQTT sim: recv %s %s\n", topic, value);   
            std::remove("mqtt.sim");
            callback(topic, (const uint8_t*) value, strlen(value) + 1);
        }
    }
    f.close();
}

bool PubSubClient::connected()
{
    return _state > 0;
}

bool PubSubClient::connect(const char *id)
{
    if (_invalid) {
        printf("MQTT sim: invalid addr, not connecting\n");   
        return false;
    }
    printf("MQTT sim: connected as %s\n", id);   
    _state = 1;
    return true;
}

void PubSubClient::subscribe(const char *topic)
{
    printf("MQTT sim: subscribed to %s\n", topic);   
}

void PubSubClient::publish(const char *topic, const uint8_t *value, size_t length, bool persist)
{
    if (! connected()) return;
    std::ofstream f;
    f.open("mqttpub.sim", std::ios_base::app);
    f << topic << " " << value << std::endl;
    f.close();
}

void PubSubClient::setServer(const char *addr, uint16_t port)
{
    printf("MQTT sim: server %s:%d\n", addr, port);
    _invalid = (strcmp(addr, "1.2.3.4") != 0);
}

void PubSubClient::setCallback(cbtype f)
{
    callback = f;
}
