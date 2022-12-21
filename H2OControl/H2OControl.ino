#if defined(ESP32)
#include <esp_bt.h>
#endif
#include "src/Elements.h"
#include "src/Constants.h"
#include "src/Console.h"

void setup() {
#if defined(ESP32)
  setCpuFrequencyMhz(80);
  esp_bt_controller_disable();
#endif
  elements_setup();
}

void loop() {
    elements_loop();
}
