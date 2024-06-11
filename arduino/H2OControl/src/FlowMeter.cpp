#include "stdlib.h"

#include "FlowMeter.h"
#include "Elements.h"
#include "Constants.h"

FlowMeter::FlowMeter(double k): k(k)
{
    rate_last_rst = Cronometer();
    rate_next_rst = Timeout(10 * SECONDS);
    reset_all();
}

void FlowMeter::reset_all()
{
    last_pulse.restart();
    last_rate = 0.0;
    rate_last_rst.restart();
    rate_next_rst.restart();
    rate_pulses = 0;

    reset_volume();
}

void FlowMeter::reset_volume()
{
    last_vol_rst.restart();
    vol_pulses = 0;
}

void FlowMeter::pulse(uint32_t quantity)
{
    last_pulse.restart();
    vol_pulses += quantity;
    rate_pulses += quantity;
}

void FlowMeter::eval()
{
    if (rate_next_rst.pending()) {
        return;
    }
    double volume = pulse_volume() * rate_pulses;
    double minutes = rate_last_rst.elapsed() / (60.0 * SECONDS);
    last_rate = volume / minutes;
    rate_last_rst.restart();
    rate_pulses = 0;
}

double FlowMeter::pulse_volume() const
{
    // 1L/min converted to L/sec, than divided by pulses/s
    return (1.0 / 60.0) / k;
}

double FlowMeter::volume() const
{
    return vol_pulses * pulse_volume();
}

double FlowMeter::rate() const
{
    return last_rate;
}
