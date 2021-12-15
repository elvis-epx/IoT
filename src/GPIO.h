#ifndef __GPIO_H
#define __GPIO_H

#include <cinttypes>

class GPIO
{
public:
	GPIO();
	void eval();
	void pulse();
	uint32_t read_level_sensors();
	uint32_t read_switches();
	void write_output(uint32_t bitmap, uint32_t mask);

private:
	uint32_t read();
	int pulses;
	uint32_t output_bitmap;
};

#endif
