#ifndef UNDER_TEST
#include <DHT.h>
#endif

#include "Sensor.h"
#include "Elements.h"
#include "Constants.h"
#include "LogDebug.h"

#ifndef UNDER_TEST
DHT dht(DHTPIN, DHTTYPE);
#endif

Sensor::Sensor()
{
    _humidity = _temperature = NAN;
    read_time = Timeout(60 * SECONDS);
    read_time.advance();
#ifndef UNDER_TEST
    dht.begin();
#endif
}

float Sensor::temperature() const
{
    return _temperature;
}

float Sensor::humidity() const
{
    return _humidity;
}

void Sensor::eval()
{
    if (read_time.pending()) {
        return;
    }
#ifndef UNDER_TEST
    _humidity = dht.readHumidity();
    _temperature = dht.readTemperature();
#endif
    Log::d("Temperature", _temperature);
    Log::d("Humidity", _humidity);
}
