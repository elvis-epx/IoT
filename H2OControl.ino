#include "src/Plant.h"

static const double level_sensors[] = LEVEL_SENSORS;
static const uint32_t flow_rates[] = FLOWRATES;

Ptr<GPIO> gpio;
Ptr<Pump> pump;
Ptr<FlowMeter> flowmeter;
Ptr<LevelMeter> levelmeter;
Ptr<Display> display;
Ptr<H2OStateMachine> sm;

void setup() {
	Serial.begin(9600);
	Serial.println("Setup");
	gpio = Ptr<GPIO>(new GPIO());
	Serial.println("GPIO initiated");
	pump = Ptr<Pump>(new Pump());
	Serial.println("Pump initiated");
	flowmeter = Ptr<FlowMeter>(new FlowMeter(FLOWMETER_PULSE_RATE, flow_rates));
	Serial.println("Flow meter initiated");
	levelmeter = Ptr<LevelMeter>(new LevelMeter(level_sensors, TANK_CAPACITY));
	Serial.println("Level meter initiated");
	display = Ptr<Display>(new Display());
	Serial.println("Display initiated");
	sm = Ptr<H2OStateMachine>(new H2OStateMachine());
	Serial.println("State machine initiated");

	sm->start();

	Serial.println("Setup ok");
}

void loop() {
	Serial.println(millis());
	gpio->eval();
	flowmeter->eval();
	levelmeter->eval();
	sm->eval();
	display->eval();
}
