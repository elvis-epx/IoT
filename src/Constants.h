#ifndef __CONSTANTS_H
#define __CONSTANTS_H

#define TANK_CAPACITY 1000.0 // liters
// level that, if lost, causes the pump to start up
// should not be the 100% to avoid many short pumping cycles
#define PUMP_THRESHOLD 80.0 // %
#define LEVEL_SENSORS {20.0, 40.0, 60.0, 80.0, 100.0, 0.0}

#define FLOWMETER_PULSE_RATE 4.8 // in pulses/s when flow is 1L/min
#define ESTIMATED_PUMP_FLOWRATE 14.5 // in L/min

// pipes between pump and flow meter
#define PIPE_DIAMETER 25.0 // in mm
#define PIPE_LENGTH   75.0 // in m

// time spans to measure average flow rate
#define FLOWRATE_INSTANT (10 * SECONDS)
#define FLOWRATE_SHORT   (2 * MINUTES)
#define FLOWRATE_LONG    (30 * MINUTES)

#define FLOWRATES {FLOWRATE_INSTANT, FLOWRATE_SHORT, FLOWRATE_LONG}

/* time that pump stays off after being on, no matter the level */
#define PUMP_REST_TIME (5 * MINUTES)

/* minimum time to start checking if there is flow */
#define MINIMUM_FLOW_LATENCY (30 * SECONDS)

/* Time tolerance of no-flow condition is
 * tolerance x (pipe_capacity / estimated flow)
 */
#define FLOW_DELAY_TOLERANCE 2.0

/* Short-term (2-min window) low flow failure threshold is:
 * estimated flow x tolerance (which must be 0 < x < 1)
 */
#define LOWFLOW_SHORT_TOLERANCE 0.25

/* Time to recover after low flow failure (see above) */
#define LOWFLOW_SHORT_RECOVERY (2 * 60 * MINUTES)

/* Same as FLOW_DELAY_TOLERANCE but for a 30-min window */
#define LOWFLOW_LONG_TOLERANCE 0.33

/* Time to recover after low flow failure (see above) */
#define LOWFLOW_LONG_RECOVERY (12 * 60 * MINUTES)

/* failure to level to increase after (volume x tolerance) pumped 
 * e.g. if level change 80%->100% takes 200L and tolerance is 2,
 * then fails if 400L+ pumped and level does not move from 80%.
 */
#define LEVEL_FAIL_TOLERANCE 2.0

/* Time to restart operation after level failure (see above) */
#define LEVEL_FAIL_RECOVERY (12 * 60 * MINUTES)

/* Stops pump after (tolerance x tank volume) pumped, regardless the level */
#define PUMP_TIMEOUT_TOLERANCE 2.0

/* Time to recover after pump timeout as described above */
#define PUMP_TIMEOUT_RECOVERY (2 * 60 * MINUTES)

#define RELAY_INVERSE_LOGIC true /* for 3V3 relay modules with inverse pin logic */
// FIXME move MyGPIO native pand MCP23017 pin config here

#define NVRAM_CHAPTER "H2OControl"

#define PUB_UPTIME "stat/H2OControl/Uptime"
#define PUB_STATE "stat/H2OControl/State"
#define PUB_LEVEL1 "stat/H2OControl/Level1"
#define PUB_LEVEL2 "stat/H2OControl/Level2"
#define PUB_LEVELERR "stat/H2OControl/LevelErr"
#define PUB_FLOWINST "stat/H2OControl/FLowInst"
#define PUB_FLOWSHORT "stat/H2OControl/FlowShort"
#define PUB_FLOWLONG "stat/H2OControl/FlowLong"
#define PUB_EFFICIENCY "stat/H2OControl/Efficiency"
#define PUB_OVERRIDEON "stat/H2OControl/OverrideOn"
#define PUB_OVERRIDEOFF "stat/H2OControl/OverrideOff"

#define SUB_OVERRIDEON "cmnd/H2OControl/OverrideOn"
#define SUB_OVERRIDEOFF "cmnd/H2OControl/OverrideOff"

#define PUB_LOGDEBUG_TOPIC "tele/H2OControl/logdebug"
#define SUB_OTA_TOPIC "cmnd/H2OControl/OTA"
#define OTA_PASSWORD "abracadabra"
#define MQTT_RELAY_ID "H2OControl"

#endif
