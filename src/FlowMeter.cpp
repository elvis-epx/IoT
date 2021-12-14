#include "FlowMeter.h"
#include "Plant.h"

FlowMeter::FlowMeter(double k): k(k)
{
	reset();
}

void FlowMeter::reset()
{
	since = last_pulse = partial_since = now();
	pulses = partial_pulses = 0;
	last_rate = 0;
}

void FlowMeter::pulse()
{
	++pulses;
	++partial_pulses;
	last_pulse = now();
}

void FlowMeter::eval()
{
	Timestamp Now = now();
	if ((Now - partial_since) > 10 * SECONDS) {
		double volume = pulse_volume() * partial_pulses;
		double minutes = (Now - partial_since) / (60.0 * SECONDS);
		last_rate = volume / minutes;
		partial_since = Now;
		partial_pulses = 0;
	}
}

Timestamp FlowMeter::last_movement() const
{
	return now() - last_pulse;
}

double FlowMeter::pulse_volume() const
{
	// 1L/min converted to L/sec, than divided by pulses/s
	return (1.0 / 60.0) / k;
}

double FlowMeter::volume() const
{
	return pulses * pulse_volume();
}

double FlowMeter::rate() const
{
	return last_rate;
}
