#include "Plant.h"
#include "LevelMeter.h"

LevelMeter::LevelMeter(const double levels[], double capacity):
	levels(levels), capacity(capacity)
{
	current_level = 100;
	last_eval = 0;
	last_change = 0;
	failure = false;
}

bool LevelMeter::failure_detected() const
{
	return failure;
}

void LevelMeter::eval()
{
	Timestamp Now = now();
	if ((Now - last_eval) < 1000) {
		return;
	}
	last_eval = Now;

	last_bitmap = gpio->read_level_sensors();

	// display.debug("sensor bitmap", (int) last_bitmap);

	double new_level = 0;
	failure = false;

	int last_off = -1;

	for (int i = 0; levels[i] != 0; ++i) {
		// pull-up logic
		bool bit = !(last_bitmap & (0x01 << i));
		// display.debug("\tsw  ", i);
		// display.debug("\tbit ", bit ? "On" : "Off");

		if (bit) {
			// sensor is ON, level is at least here
			new_level = levels[i];

			if (last_off > -1) {
				// there was an OFF sensor below
				failure = true;
				// display.debug("sensor failure", last_off);
			}
		} else {
			// sensor is OFF
			last_off = i;
		}
	}


	// display.debug("level", current_level);
	// display.debug("failure", failure);

	if (new_level != current_level) {
		current_level = new_level;
		last_change = now();
		flowmeter->reset_volume();
	}
}

Timestamp LevelMeter::last_movement() const
{
	return last_change;
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

uint32_t LevelMeter::bitmap() const
{
	return last_bitmap;
}
