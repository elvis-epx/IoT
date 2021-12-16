#include "stdlib.h"

#include "FlowMeter.h"
#include "Plant.h"

FlowMeter::FlowMeter(double k, const uint32_t* rate_intervals):
		k(k), rate_intervals(rate_intervals)
{
	rate_count = 0;
	while (rate_intervals[rate_count++] > 0);
	last_rates = Ptr<double>((double*) calloc(rate_count, sizeof(double)));
	rate_last_reset = Ptr<Timestamp>((Timestamp*) calloc(rate_count, sizeof(Timestamp)));
	rate_pulses = Ptr<uint32_t>((uint32_t*) calloc(rate_count, sizeof(uint32_t)));

	reset_all();
}

void FlowMeter::reset_all()
{
	Timestamp Now = now();
	last_pulse = Now;
	for (size_t i = 0; i < rate_count; ++i) {
		last_rates[i] = -1;
		rate_last_reset[i] = Now;
		rate_pulses[i] = 0;
	}
	reset_volume();
}

void FlowMeter::reset_volume()
{
	last_vol_reset = now();
	vol_pulses = 0;
}

void FlowMeter::pulse(uint32_t quantity)
{
	last_pulse = now();
	vol_pulses += quantity;
	for (size_t i = 0; i < rate_count; ++i) {
		rate_pulses[i] += quantity;
	}
}

void FlowMeter::eval()
{
	Timestamp Now = now();

	for (size_t i = 0; i < rate_count; ++i) {
		if ((Now - rate_last_reset[i]) > rate_intervals[i]) {
			double volume = pulse_volume() * rate_pulses[i];
			double minutes = (Now - rate_last_reset[i]) / (60.0 * SECONDS);
			last_rates[i] = volume / minutes;
			rate_last_reset[i] = Now;
			rate_pulses[i] = 0;
		}
	}
}

Timestamp FlowMeter::last_movement() const
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

double FlowMeter::rate(uint32_t interval) const
{
	for (size_t i = 0; i < rate_count; ++i) {
		if (rate_intervals[i] >= interval) {
			return last_rates[i];
		}
	}
	return 0;
}
