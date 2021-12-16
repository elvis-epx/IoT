#ifndef __LEVELMETER_H
#define __LEVELMETER_H

#include "Timestamp.h"

class LevelMeter
{
public:
	// Levels, in % of each of the sensors
	// must be in ascending order
	// must terminate with 100, 0
	LevelMeter(const double levels[], double capacity);

	void eval();

	double level_pct() const; // in %
	double level_liters() const; // in liters
	double next_level_liters() const; // in liters
	bool failure_detected() const;
	uint32_t bitmap() const;
	Timestamp last_movement() const;

private:

	Timestamp last_eval;
	Timestamp last_change;
	const double *levels;
	double current_level;
	double capacity; // estimated tank capacity in liters

	bool failure;
	uint32_t last_bitmap;
};

#endif
