#include "GPIO.h"
#include "Plant.h"

#ifdef UNDER_TEST
#include <iostream>
#include <fstream>
#endif

GPIO::GPIO()
{
	pulses = 0;
	output_bitmap = 0;
	write_output(output_bitmap, ~0);
}

uint32_t GPIO::read_switches()
{
	return (read() >> 5) & 0x3;
}

uint32_t GPIO::read_level_sensors()
{
	return read() & 0x1f;
}

uint32_t GPIO::read()
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

void GPIO::write_output(uint32_t bitmap, uint32_t bitmask)
{
	output_bitmap = (output_bitmap & ~bitmask) | bitmap;
#ifdef UNDER_TEST
	std::ofstream f;
	f.open("gpio2.txt");
	f << output_bitmap;
	f.close();
#endif
}

void GPIO::pulse()
{
	// Flow meter pulse
	// do as little as possible, since it may be called
	// by an interrupt handler
	++pulses;
}

void GPIO::eval()
{
#ifdef UNDER_TEST
	int qty = 0;
	std::ifstream f;
	f.open("pulses.txt");
	f >> qty;
	f.close();
	std::remove("pulses.txt");
	pulses += qty;
#endif
	if (pulses > 0) {
		flowmeter.pulse(pulses);
		pulses = 0;
	}
}
