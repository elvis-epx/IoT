#include "Plant.h"
#include "LevelMeter.h"

LevelMeter::LevelMeter(const double levels[], double capacity):
	levels(levels), capacity(capacity)
{
	current_level = 100;
	current_law = Law_Normal;
	last_eval = 0;
}

void LevelMeter::eval()
{
	Timestamp Now = now();
	if ((Now - last_eval) < 1000) {
		return;
	}
	last_eval = Now;

	last_bitmap = gpio.read_level_sensors();

	// display.debug("sensor bitmap", (int) last_bitmap);

	current_level = 0;

	int i = 0;
	int j = i;
	bool sensor_group = false;
	int last_off = -1;

	do {
		bool bit = last_bitmap & (0x01 << i);

		if (levels[i] == levels[j]) {
			// still in the same group (sensors at the same level)
			sensor_group = sensor_group || bit;
			continue;
		}

		// group closed
		if (sensor_group) {
			// sensor is ON, level is at least in this level
			current_level = levels[j];

			if (last_off > -1) {
				// there was an OFF sensor below
				current_law = Law_SensorFailed;
				// display.debug("sensor failure", last_off);
			}
		} else {
			// sensor is OFF
			last_off = j;
		}

		// move onto new sensor group
		j = i;
		sensor_group = bit;

	} while (levels[i++] != 0);

	// display.debug("level", current_level);
	// display.debug("law", current_law);

	if (current_law <= Law_DisagreementAtTop) {
		// Disagreement of sensors at water level may clear
		current_law = Law_Normal;
	} else {
		// Errors already found are severe enough
		return;
	}

	// Detect disagreement between sensors

	i = 0;
	j = i;
	bool sensor_group_or = false;
	bool sensor_group_and = true;

	do {
		bool bit = last_bitmap & (0x01 << i);

		if (levels[i] == levels[j]) {
			sensor_group_or = sensor_group_or || bit;
			sensor_group_and = sensor_group_and && bit;
			continue;
		}

		if (sensor_group_or != sensor_group_and) {
			if (levels[j] == current_level) {
				// disagreement at current water level
				// display.debug("sensor disagreement at top", j);
				if (current_law < Law_DisagreementAtTop) {
					current_law = Law_DisagreementAtTop;
				}
			} else {
				// disagreement below water level
				// display.debug("sensor disagreement", j);
				current_law = Law_Disagreement;
			}
		}

		j = i;
		sensor_group_or = sensor_group_and = bit;

	} while (levels[i++] != 0);
}

int LevelMeter::law() const
{
	return current_law;
}

double LevelMeter::level_pct() const
{
	return current_level;
}

double LevelMeter::level_liters() const
{
	return current_level * capacity / 100;
}

double LevelMeter::next_level_liters() const
{
	for (int i = 0; levels[i] > 0; ++i) {
		if (levels[i] > current_level) {
			return levels[i] * capacity / 100;
		}
	}

	return capacity;
}

int LevelMeter::bitmap() const
{
	return last_bitmap;
}
