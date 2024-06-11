#ifndef _WIFI_H
#define _WIFI_H

#define WL_CONNECTED 1
#define WL_NOTCONNECTED 0

class WiFiClient {
};

class AuxAddr2 {
public:
    const char *c_str();
};

class AuxAddr {
public:
    AuxAddr2 toString();
};

class WiFiSingleton {
public:
    WiFiSingleton();
    void begin(const char *ssid);
    void begin(const char *ssid, const char *password);
    int status();
    AuxAddr localIP();
private:
    int _status;
};

extern WiFiSingleton WiFi;

#endif
