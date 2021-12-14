#ifndef __FLOWMETER_H
#define __FLOWMETER_H

#include "Timestamp.h"

class FlowMeter
{
public:
	// k = pulses per second when flow is 1L/min
	FlowMeter(double k);
	void reset();
	void pulse();

	Timestamp last_movement() const; // time since last pulse received
	double pulse_volume() const; // volume of 1 pulse, in liters
	double volume() const; // in liters, since reset
	double rate() const; // in liters per minute, moving average

private:
	double k;
	Timestamp since;
	uint32_t pulses;
	Timestamp last_pulse;
	double pulse_length_avg;
};

#endif
