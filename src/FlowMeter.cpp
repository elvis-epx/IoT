#include "stdlib.h"

#include "FlowMeter.h"
#include "Elements.h"
#include "Constants.h"

FlowMeter::FlowMeter(double k, const uint32_t* rate_intervals): k(k)
{
    for (size_t i = 0; rate_intervals[i] > 0; ++i) {
        this->rate_intervals.push_back(rate_intervals[i]);
        this->last_rates.push_back(0.0);
        this->rate_next_rst.push_back(Timeout(rate_intervals[i]));
        this->rate_last_rst.push_back(Cronometer());
        this->rate_pulses.push_back(0);
    }

    reset_all();
}

void FlowMeter::reset_all()
{
    last_pulse.restart();
    for (size_t i = 0; i < rate_intervals.count(); ++i) {
        last_rates[i] = -1;
        rate_last_rst[i].restart();
        rate_next_rst[i].restart();
        rate_pulses[i] = 0;
    }
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
    for (size_t i = 0; i < rate_intervals.count(); ++i) {
        rate_pulses[i] += quantity;
    }
}

void FlowMeter::eval()
{
    for (size_t i = 0; i < rate_intervals.count(); ++i) {
        if (rate_next_rst[i].pending()) {
            continue;
        }
        double volume = pulse_volume() * rate_pulses[i];
        double minutes = rate_last_rst[i].elapsed() / (60.0 * SECONDS);
        last_rates[i] = volume / minutes;
        rate_last_rst[i].restart();
        rate_pulses[i] = 0;
    }
}

Cronometer FlowMeter::last_movement() const
{
    return last_pulse;
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

double FlowMeter::expected_volume() const
{
    return ESTIMATED_PUMP_FLOWRATE * last_vol_rst.elapsed() / (1.0 * MINUTES);
}

double FlowMeter::rate(uint32_t interval) const
{
    for (size_t i = 0; i < rate_intervals.count(); ++i) {
        if (rate_intervals[i] == interval) {
            return last_rates[i];
        }
    }
    return -2;
}
