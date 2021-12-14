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

private:
	int pulses;
};

#endif
