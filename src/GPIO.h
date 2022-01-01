#ifndef __GPIO_H
#define __GPIO_H

#include "inttypes.h"

class GPIO
{
public:
	GPIO();
	void eval();
	void pulse();
	uint32_t read_level_sensors();
	bool read_switch(uint32_t bitmap);
	void write_pump(bool state);
	
	static const uint32_t SWITCH_ON_MANUAL = 0x01;
	static const uint32_t SWITCH_OFF_MANUAL = 0x02;
	static const uint32_t SWITCH_DEGRADED = 0x04;
private:
	static const uint32_t PUMP = 0x01;

	uint32_t read_switches();
	void write_output(uint32_t bitmap, uint32_t mask);
	uint32_t read();

	int pulses;
	uint32_t output_bitmap;
};

#endif
