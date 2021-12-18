#include "src/Elements.h"
#include "src/Constants.h"

static const double level_sensors[] = LEVEL_SENSORS;
static const uint32_t flow_rates[] = FLOWRATES;

Ptr<GPIO> gpio;
Ptr<Pump> pump;
Ptr<FlowMeter> flowmeter;
Ptr<LevelMeter> levelmeter;
Ptr<Display> display;
Ptr<H2OStateMachine> sm;

// in ESP32 dev kit, "pin 13" w/ built-in LED is actually pin 2
const int heartbeat_led = 2;

void setup() {
	setCpuFrequencyMhz(80);
	esp_bt_controller_disable();
	Serial.begin(9600);
	Serial.println("Setup");
	
	pinMode(heartbeat_led, OUTPUT);
	digitalWrite(heartbeat_led, HIGH);

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

bool heartbeat = LOW;

void loop() {
	digitalWrite(heartbeat_led, heartbeat);
	heartbeat = !heartbeat;
	
	gpio->eval();
	flowmeter->eval();
	levelmeter->eval();
	sm->eval();
	display->eval();
	
	delay(250);
}