#include "Elements.h"
#include "Constants.h"
#include "Timer.h"
#include "Console.h"
#if defined(ESP32)
#include <esp_task_wdt.h>
#endif
#ifdef ESP8266
#endif

Ptr<Sensor> sensor;
Ptr<MQTT> mqtt;
Preferences prefs;

static Timeout watchdog;

void elements_setup() {
  console_setup();

#if defined(ESP32)
  esp_task_wdt_init(15, true);
  esp_task_wdt_add(NULL);
#endif
#ifdef ESP8266
  ESP.wdtDisable();
#endif
  watchdog = Timeout(500 * MILISSECONDS);

  sensor = Ptr<Sensor>(new Sensor());
  console_println("Sensor initiated");
  mqtt = Ptr<MQTT>(new MQTT());
  mqtt->start();
  console_println("MQTT initiated");
  console_println("Setup ok");
  console_println("Type !help for available commands.");
}

void elements_loop() {
  mqtt->eval();
  sensor->eval();
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
