#if defined(ESP32)
#include <esp_bt.h>
#endif
#include "src/Elements.h"
#include "src/Constants.h"

static const double level_sensors[] = LEVEL_SENSORS;
static const uint32_t flow_rates[] = FLOWRATES;

Ptr<MyGPIO> gpio;
Ptr<Pump> pump;
Ptr<FlowMeter> flowmeter;
Ptr<LevelMeter> levelmeter;
Ptr<Display> display;
Ptr<H2OStateMachine> sm;
Ptr<MQTT> mqtt;

// GPIO 2 = D4 in ESP8266 NodeMCU
const int heartbeat_led = 2;

void setup() {
#if defined(ESP32)
  setCpuFrequencyMhz(80);
  esp_bt_controller_disable();
#endif
  Serial.begin(115200);
  Serial.println("Setup");

  pinMode(heartbeat_led, OUTPUT);
  digitalWrite(heartbeat_led, HIGH);

  gpio = Ptr<MyGPIO>(new MyGPIO());
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
  mqtt = Ptr<MQTT>(new MQTT());
  Serial.println("MQTT initiated");

  sm->start();
  mqtt->start();

  Serial.println("Setup ok");
}

bool heartbeat = LOW;
int64_t next_heartbeat = 0;

void loop() {
  if (now() > next_heartbeat) {
  	digitalWrite(heartbeat_led, heartbeat);
  	heartbeat = !heartbeat;
  	next_heartbeat = now() + 250;
  }

  gpio->eval();
  flowmeter->eval();
  levelmeter->eval();
  sm->eval();
  display->eval();
  mqtt->eval();
}
