#include "GPIO.h"
#include "Elements.h"

#ifdef UNDER_TEST

#include <iostream>
#include <fstream>

#else

#include <Arduino.h>

static void pulse_trampoline()
{
	gpio->pulse();
}

#endif

GPIO::GPIO()
{
	pulses = 0;
	output_bitmap = 0;

#ifndef UNDER_TEST
	// level meter
	pinMode(2, INPUT_PULLUP);
	pinMode(3, INPUT_PULLUP);
	pinMode(4, INPUT_PULLUP);
	pinMode(5, INPUT_PULLUP);
	pinMode(6, INPUT_PULLUP);
	// manual override switches
	pinMode(7, INPUT_PULLUP);
	pinMode(8, INPUT_PULLUP);
	// flow meter
	pinMode(9, INPUT_PULLUP);
	attachInterrupt(digitalPinToInterrupt(9), pulse_trampoline, RISING);
	// pump
	pinMode(11, OUTPUT);
#endif
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
	uint32_t bitmap = 0;
#ifdef UNDER_TEST
	std::ifstream f;
	f.open("gpio.txt");
	f >> bitmap;
	f.close();
#else
	for (int i = 2; i <= 9; ++i) {
		bitmap |= (digitalRead(i) ? 1 : 0) << (i - 2);
	}
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
#else
	digitalWrite(11, output_bitmap & 0x01);
	digitalWrite(13, output_bitmap & 0x02);
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
	while (qty-- > 0) {
		pulse();
	}
#endif
	if (pulses > 0) {
		flowmeter->pulse(pulses);
		pulses = 0;
	}
}
