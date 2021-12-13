#include "FlowMeter.h"

FlowMeter::FlowMeter(double k): k(k)
{
	reset();
}

void FlowMeter::reset()
{
	since = last_pulse = now();
	pulses = 0;
	pulse_length_avg = 86400000.0; // in milisseconds
}

void FlowMeter::pulse()
{
	++pulses;
	Timestamp now_ = now();
	double last_pulse_length = now_ - last_pulse;
	last_pulse = now_;

	// cannot handle pulses shorter than 1ms
	if (last_pulse_length <= 1.0) {
		last_pulse_length = 1.0;
	}
	pulse_length_avg = (0.995 * pulse_length_avg) + (0.005 * last_pulse_length);
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
	// convert pulse length in ms to pulses/min
	double pulses_per_min = 60000.0 / pulse_length_avg;
	// multiply by estimated volume of each pulse
	return pulse_volume() * pulses_per_min;
}
