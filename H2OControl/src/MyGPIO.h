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
private:
    uint32_t read();

    int pulses;
};

#endif
