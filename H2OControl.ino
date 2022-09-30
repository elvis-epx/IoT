#if defined(ESP32)
#include <esp_bt.h>
#include <Preferences.h>
#endif
#include "src/Elements.h"
#include "src/Constants.h"
#include "src/Console.h"

static const double level_sensors[] = LEVEL_SENSORS;
static const uint32_t flow_rates[] = FLOWRATES;

Ptr<MyGPIO> gpio;
Ptr<Pump> pump;
Ptr<FlowMeter> flowmeter;
Ptr<LevelMeter> levelmeter;
Ptr<Display> display;
Ptr<H2OStateMachine> sm;
Ptr<MQTT> mqtt;
Preferences prefs;

// GPIO 2 = D4 in ESP8266 NodeMCU
const int heartbeat_led = 2;

void setup() {
#if defined(ESP32)
  setCpuFrequencyMhz(80);
  esp_bt_controller_disable();
#endif
  console_setup();

  pinMode(heartbeat_led, OUTPUT);
  digitalWrite(heartbeat_led, HIGH);

  gpio = Ptr<MyGPIO>(new MyGPIO());
  console_println("GPIO initiated");
  pump = Ptr<Pump>(new Pump());
  console_println("Pump initiated");
  flowmeter = Ptr<FlowMeter>(new FlowMeter(FLOWMETER_PULSE_RATE, flow_rates));
  console_println("Flow meter initiated");
  levelmeter = Ptr<LevelMeter>(new LevelMeter(level_sensors, TANK_CAPACITY));
  console_println("Level meter initiated");
  display = Ptr<Display>(new Display());
  console_println("Display initiated");
  sm = Ptr<H2OStateMachine>(new H2OStateMachine());
  console_println("State machine initiated");
  mqtt = Ptr<MQTT>(new MQTT());
  console_println("MQTT initiated");

  sm->start();
  mqtt->start();

  console_println("Setup ok");
  console_println("Type !help for available commands.");
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
  console_eval();
}
