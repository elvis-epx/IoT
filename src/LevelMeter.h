#ifndef __LEVELMETER_H
#define __LEVELMETER_H

#include "Timestamp.h"

class LevelMeter
{
public:
	// Levels, in % of each of the sensors
	// must be in ascending order
	// must terminate with 100, 0
	// multiple sensors at the same level are supported for robustness
	LevelMeter(const double levels[], double capacity);

	double level_pct(); // in %
	double level_liters(); // in liters
	double next_level_liters(); // in liters
	int law(); // see next constants

	static const int Law_Normal = 0;
	static const int Law_DisagreementAtTop = 1;
	static const int Law_Disagreement = 2;
	static const int Law_SensorFailed = 3;

private:
	void interpret_sensors();

	const double *levels;
	double current_level;
	double capacity; // estimated tank capacity in liters
	int current_law;
	uint32_t failed_sensor_map;
};

#endif
