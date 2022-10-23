#include "Elements.h"
#include "Constants.h"
#include "Vector.h"
#include "Timer.h"
#include "Console.h"
#include <Wire.h>
#if defined(ESP32)
#include <esp_task_wdt.h>
#endif
#ifdef ESP8266
#endif

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

static Timeout watchdog;

void elements_setup() {
    console_setup();

#if defined(ESP32)
    esp_task_wdt_init(3, true);
    esp_task_wdt_add(NULL);
#endif
#ifdef ESP8266
    ESP.wdtDisable()
#endif
    watchdog = Timeout(500 * MILISSECONDS);

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

void elements_loop() {
    gpio->eval();
    flowmeter->eval();
    levelmeter->eval();
    sm->eval();
    display->eval();
    mqtt->eval();
    console_eval();
    
    if (watchdog.pending()) {
        return;
    }

#if defined(ESP32)
    esp_task_wdt_reset();
#endif
#ifdef ESP8266
    ESP.wdtFeed();
#endif
}

static bool i2c_started = false;

void i2c_begin()
{
    if (i2c_started) return;
    
    Wire.begin();
    i2c_started = true;
}
