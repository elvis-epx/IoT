#ifndef __FLOWMETER_H
#define __FLOWMETER_H

#include <stddef.h>
#include "Timestamp.h"
#include "Pointer.h"

class FlowMeter
{
public:
	// k = pulses per second when flow is 1L/min
	// rate_intervals: 0-terminated list of time intervals
	// to measure rate. In miliseconds.

	FlowMeter(double k, const int *rate_intervals);
	void reset();
	void pulse();
	void eval();

	Timestamp last_movement() const; // time since last pulse received
	double pulse_volume() const; // volume of 1 pulse, in liters
	double volume() const; // in liters, since reset

	// in liters per minute for the given time interval
	double rate(int interval) const;

private:
	double k;
	Timestamp last_reset;
	uint32_t pulses;
	Timestamp last_pulse;

	const int *rate_intervals;
	size_t rate_count;
	Ptr<double> last_rates;
	Ptr<Timestamp> rate_last_reset;
	Ptr<uint32_t> rate_pulses;
};

#endif
