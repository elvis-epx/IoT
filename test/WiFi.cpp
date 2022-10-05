#include "WiFi.h"

WiFiSingleton WiFi;

const char *AuxAddr2::c_str()
{
    return "1.2.3.4";
}

AuxAddr2 AuxAddr::toString()
{
    return AuxAddr2();
}

WiFiSingleton::WiFiSingleton()
{
    _status = WL_NOTCONNECTED;
}

void WiFiSingleton::begin(const char *ssid)
{
    _status = WL_CONNECTED;
}

void WiFiSingleton::begin(const char *ssid, const char *password)
{
    _status = WL_CONNECTED;
}
int WiFiSingleton::status()
{
    return _status;
}

AuxAddr WiFiSingleton::localIP()
{
    return AuxAddr();
}
