#ifndef __PLANT_H
#define __PLANT_H

#include "Pump.h"
#include "FlowMeter.h"
#include "LevelMeter.h"
#include "GPIO.h"
#include "Display.h"
#include "H2OStateMachine.h"

#define TANK_CAPACITY 1000.0 // liters
#define LOWLEVEL_THRESHOLD 80.0 // %

#define FLOWMETER_PULSE_RATE 4.8 // in pulses/s when flow is 1L/min
#define LEVEL_SENSORS {25.0, 50.0, 75.0, 100.0, 100.0, 0.0}
#define ESTIMATED_PUMP_FLOWRATE (1100.0 / 60) // in L/min

extern GPIO gpio;
extern Pump pump;
extern FlowMeter flowmeter;
extern LevelMeter levelmeter;
extern Display display;
extern H2OStateMachine sm;

#endif
