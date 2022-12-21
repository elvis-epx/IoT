#ifndef __SENSOR_H
#define __SENSOR_H

#include "Timer.h"

class Sensor
{
public:
    Sensor();
    float temperature() const;
    float humidity() const;
    void eval();

private:
    Timeout read_time;
    float _temperature;
    float _humidity;
};

#endif
