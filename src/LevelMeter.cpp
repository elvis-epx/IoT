#include "Plant.h"
#include "LevelMeter.h"

LevelMeter::LevelMeter(const double levels[], double capacity):
	levels(levels), capacity(capacity)
{
	current_level = 100;
	current_law = Law_Normal;
}

void LevelMeter::interpret_sensors()
{
	uint32_t bitmap = gpio.read_level_sensors();

	// if all sensors are on, the level must be 100%
	current_level = 100;

	int i = 0;
	int j = i;
	bool sensor_group_or = false;
	bool sensor_group_and = true;

	do {
		if (levels[i] == levels[j]) {
			// still in the same group (sensors at the same level)
			sensor_group_or |= bitmap & (0x01 << i);
			sensor_group_and &= bitmap & (0x01 << i);
			continue;
		}

		// group closed
		if (! sensor_group_or) {
			// all sensors of the group were off
			// take level of the sensor group immediately below
			current_level = j > 0 ? levels[j - 1] : 0;
		} else if (current_level != 100) {
			// this sensor group ON, but sensor below OFF
			current_law = Law_SensorFailed;
		}

		// move onto new sensor group
		j = i;
		sensor_group_or = sensor_group_and = bitmap & (0x01 << i);

	} while (levels[i++] != 0);

	if (current_law >= Law_Disagreement) {
		// sticky errors
		return;
	}

	// Disagreement of sensors at water level clears itself
	current_law = Law_Normal;

	// Detect disagreement between sensors

	i = 0;
	j = i;
	sensor_group_or = false;
	sensor_group_and = true;

	do {
		if (levels[i] == levels[j]) {
			sensor_group_or |= bitmap & (0x01 << i);
			sensor_group_and &= bitmap & (0x01 << i);
			continue;
		}

		if (sensor_group_or != sensor_group_and) {
			if (levels[j] == current_level) {
				// disagreement at current water level
				if (current_law < Law_DisagreementAtTop) {
					current_law = Law_DisagreementAtTop;
				}
			} else {
				// disagreement below water level
				current_law = Law_Disagreement;
			}
		}

		j = i;
		sensor_group_or = sensor_group_and = bitmap & (0x01 << i);

	} while (levels[i++] != 0);
}

int LevelMeter::law()
{
	interpret_sensors();

	return current_law;
}

double LevelMeter::level_pct()
{
	interpret_sensors();

	return current_level;
}

double LevelMeter::level_liters() 
{
	interpret_sensors();

	return current_level * capacity / 100;
}

double LevelMeter::next_level_liters()
{
	interpret_sensors();

	for (int i = 0; levels[i] > 0; ++i) {
		if (failed_sensor_map & (0x01 << i)) {
			continue;
		}
		if (levels[i] > current_level) {
			return levels[i] * capacity / 100;
		}
	}

	return capacity;
}
