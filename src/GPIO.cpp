#include "GPIO.h"
#include "Plant.h"

#ifdef UNDER_TEST
#include <iostream>
#include <fstream>
#endif

GPIO::GPIO()
{
	pulses = 0;
}

uint32_t GPIO::read_level_sensors()
{
	uint32_t bitmap;
#ifdef UNDER_TEST
	std::ifstream f;
	f.open("gpio.txt");
	f >> bitmap;
	f.close();
#endif
	return bitmap;
}

void GPIO::pulse()
{
	// Flow meter pulse
	// do as little as possible, since it may be called
	// by an interrupt handler
	++pulses;
}

void GPIO::deliver_pulse()
{
	if (pulses > 0) {
		--pulses;
		flowmeter.pulse();
	}
}
