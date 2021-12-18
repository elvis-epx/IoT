#ifndef __CONSTANTS_H
#define __CONSTANTS_H

#define TANK_CAPACITY 1000.0 // liters
// ought to be the second sensor, top to bottom
#define PUMP_THRESHOLD 80.0 // %
#define LEVEL_SENSORS {20.0, 40.0, 60.0, 80.0, 100.0, 0.0}

#define FLOWMETER_PULSE_RATE 4.8 // in pulses/s when flow is 1L/min
#define ESTIMATED_PUMP_FLOWRATE (1100.0 / 60) // in L/min

// pipes between pump and flow meter
#define PIPE_DIAMETER 25.0 // in mm
#define PIPE_LENGTH   75.0 // in m

// time spans to measure average flow rate
#define FLOWRATE_INSTANT (10 * SECONDS)
#define FLOWRATE_SHORT   (2 * MINUTES)
#define FLOWRATE_LONG    (30 * MINUTES)

#define FLOWRATES {FLOWRATE_INSTANT, FLOWRATE_SHORT, FLOWRATE_LONG}

#endif
