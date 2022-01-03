#include "GPIO.h"
#include "Elements.h"

#ifdef UNDER_TEST

#include <iostream>
#include <fstream>

#else

#include <Arduino.h>
#include <Wire.h>
#include <MCP23017.h>

#define MCP23017_ADDR 0x20

MCP23017 mcp = MCP23017(MCP23017_ADDR);

static void ICACHE_RAM_ATTR pulse_trampoline()
{
	gpio->pulse();
}

#endif

#define FLOWMETER_PIN 14

GPIO::GPIO()
{
	pulses = 0;
	output_bitmap = 0;

#ifndef UNDER_TEST
	Wire.begin();
	mcp.init();

	// high bits = input. Third parameter is pullup and all-1 by default
	mcp.portMode(MCP23017Port::A, 0);
	mcp.portMode(MCP23017Port::B, 0b11111111);
	mcp.writeRegister(MCP23017Register::GPIO_A, 0x00); // reset
	mcp.writeRegister(MCP23017Register::GPIO_B, 0x00); // reset
	// flow meter
	pinMode(FLOWMETER_PIN, INPUT_PULLUP);
	attachInterrupt(digitalPinToInterrupt(FLOWMETER_PIN), pulse_trampoline, RISING);
#endif
	write_output(output_bitmap, ~0);
}

uint32_t GPIO::read_level_sensors()
{
	return read() & 0b11111;
}

uint32_t GPIO::read()
{
	uint32_t bitmap = 0;
#ifdef UNDER_TEST
	std::ifstream f;
	f.open("gpio.sim");
	f >> bitmap;
	f.close();
#else
	bitmap = mcp.readPort(MCP23017Port::B);
#endif
	return bitmap;
}

void GPIO::write_pump(bool state)
{
	write_output(state ? ~0 : 0, PUMP);
}

void GPIO::write_output(uint32_t bitmap, uint32_t bitmask)
{
	output_bitmap = (output_bitmap & ~bitmask) | (bitmap & bitmask);
#ifdef UNDER_TEST
	std::ofstream f;
	f.open("gpio2.sim");
	f << output_bitmap;
	f.close();
#else
	mcp.writePort(MCP23017Port::A, output_bitmap);
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
	f.open("pulses.sim");
	if (f.is_open()) {
		f >> qty;
		std::remove("pulses.sim");
	}
	f.close();
	while (qty-- > 0) {
		pulse();
	}
#endif
	if (pulses > 0) {
		flowmeter->pulse(pulses);
		pulses = 0;
	}
}
