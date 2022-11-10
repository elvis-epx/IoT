#ifndef __FLOWMETER_H
#define __FLOWMETER_H

#include <stddef.h>
#include "Timer.h"
#include "Vector.h"

class FlowMeter
{
public:
    // k = pulses per second when flow is 1L/min
    // rate_intervals: 0-terminated list of time intervals
    // to measure rate. In miliseconds.

    FlowMeter(double k);
    void reset_all();
    void reset_volume();
    void pulse(uint32_t);
    void eval();

    double pulse_volume() const; // volume of 1 pulse, in units
    double volume() const; // in units, since last reset

    // in volume units per minute
    double rate() const;

private:
    double k;
    Cronometer last_pulse;

    Cronometer last_vol_rst;
    uint32_t vol_pulses;

    double last_rate;
    Cronometer rate_last_rst;
    Timeout rate_next_rst;
    uint32_t rate_pulses;
};

#endif
