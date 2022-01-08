#ifndef __MYGPIO_H
#define __MYGPIO_H

#include "inttypes.h"

class MyGPIO
{
public:
	MyGPIO();
	void eval();
	void pulse();
	uint32_t read_level_sensors();
	void write_pump(bool state);
private:
	static const uint32_t PUMP = 0x01;

	void write_output(uint32_t bitmap, uint32_t mask);
	uint32_t read();

	int pulses;
	uint32_t output_bitmap;
};

#endif
