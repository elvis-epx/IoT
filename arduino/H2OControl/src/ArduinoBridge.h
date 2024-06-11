/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

// Platform-dependent functions. They are faked on Linux to run tests.

#ifndef __ARDUINO_BRIDGE
#define __ARDUINO_BRIDGE

#include "stdint.h"

uint32_t _arduino_millis();
void arduino_restart();
void arduino_pinmode(int, int);
void arduino_digitalwrite(int, bool);

#ifdef UNDER_TEST

#define OUTPUT 0
#define INPUT 1
#define INPUT_PULLUP 2

#endif

#endif
