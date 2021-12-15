#include "src/Plant.h"

static const double level_sensors[] = LEVEL_SENSORS;
static const uint32_t flow_rates[] = FLOWRATES;

GPIO gpio;
Pump pump;
FlowMeter flowmeter(FLOWMETER_PULSE_RATE, flow_rates);
LevelMeter levelmeter(level_sensors, TANK_CAPACITY);
Display display;
H2OStateMachine sm;

void setup() {
	Serial.begin(9600);
	Serial.println("setup");
	/*
	display.init();
	gpio.init();
	pump.init();
	flowmeter.init();
	levelmeter.init();
	sm.start();
	*/
	Serial.println("done");
}

void loop() {
	Serial.println("loop");
	/*
	gpio.eval();
	flowmeter.eval();
	levelmeter.eval();
	sm.eval();
	display.eval();
	*/
}
