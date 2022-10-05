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
        this->rate_last_rst.push_back(0);
        this->rate_pulses.push_back(0);
    }

    reset_all();
}

void FlowMeter::reset_all()
{
    Timestmp Now = now();
    last_puls = Now;
    for (size_t i = 0; i < rate_intervals.count(); ++i) {
        last_rates[i] = -1;
        rate_last_rst[i] = Now;
        rate_next_rst[i].restart();
        rate_pulses[i] = 0;
    }
    reset_volume();
}

void FlowMeter::reset_volume()
{
    last_vol_rst = now();
    vol_pulses = 0;
}

void FlowMeter::pulse(uint32_t quantity)
{
    last_puls = now();
    vol_pulses += quantity;
    for (size_t i = 0; i < rate_intervals.count(); ++i) {
        rate_pulses[i] += quantity;
    }
}

void FlowMeter::eval()
{
    Timestmp Now = now();

    for (size_t i = 0; i < rate_intervals.count(); ++i) {
        if (rate_next_rst[i].pending()) {
            continue;
        }
        // FIXME reuse timeout for rate_last_rst etc.
        double volume = pulse_volume() * rate_pulses[i];
        double minutes = (Now - rate_last_rst[i]) / (60.0 * SECONDS);
        last_rates[i] = volume / minutes;
        rate_last_rst[i] = Now;
        rate_pulses[i] = 0;
    }
}

Timestmp FlowMeter::last_mov() const
{
    return last_puls;
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
    return ESTIMATED_PUMP_FLOWRATE * (now() - last_vol_rst) / (1.0 * MINUTES);
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
