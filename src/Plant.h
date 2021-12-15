#ifndef __PLANT_H
#define __PLANT_H

#include "Pump.h"
#include "FlowMeter.h"
#include "LevelMeter.h"
#include "GPIO.h"
#include "Display.h"
#include "H2OStateMachine.h"

#define TANK_CAPACITY 1000.0 // liters
// ought to be just below the second sensor, top to bottom
#define LOWLEVEL_THRESHOLD 79.0 // %
#define LEVEL_SENSORS {20.0, 40.0, 60.0, 80.0, 100.0, 0.0}

#define FLOWMETER_PULSE_RATE 4.8 // in pulses/s when flow is 1L/min
#define ESTIMATED_PUMP_FLOWRATE (1100.0 / 60) // in L/min

// pipes between pump and flow meter
#define PIPE_DIAMETER 25 // in mm
#define PIPE_LENGTH   75.0 // in m

// time spans to measure average flow rate
#define FLOWRATE_INSTANT (10 * SECONDS)
#define FLOWRATE_SHORT   (2 * MINUTES)
#define FLOWRATE_LONG    (30 * MINUTES)

#define FLOWRATES {FLOWRATE_INSTANT, FLOWRATE_SHORT, FLOWRATE_LONG}

extern GPIO gpio;
extern Pump pump;
extern FlowMeter flowmeter;
extern LevelMeter levelmeter;
extern Display display;
extern H2OStateMachine sm;

#endif
