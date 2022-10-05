#ifndef _PUBSUBCLIENT_H
#define _PUBSUBCLIENT_H

#include "WiFi.h"
#include <cstdlib>
#include <cstdint>

typedef void (*cbtype)(const char*, const uint8_t*, unsigned int);

class PubSubClient {
public:
    PubSubClient(WiFiClient& ap);
    int state();
    void loop();
    bool connected();
    bool connect(const char *id);
    void subscribe(const char *topic);
    void publish(const char *topic, const uint8_t *value, size_t length, bool persist);
    void setServer(const char *addr, uint16_t port);
    void setCallback(cbtype f);
private:
    int _state;
    bool _invalid;
    cbtype callback;
};

#endif
