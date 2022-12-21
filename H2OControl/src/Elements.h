#ifndef __ELEMENTS_H
#define __ELEMENTS_H

#include <Preferences.h>
#include "Pointer.h"
#include "FlowMeter.h"
#include "LevelMeter.h"
#include "MyGPIO.h"
#include "Display.h"
#include "MQTT.h"

extern Ptr<MyGPIO> gpio;
extern Ptr<FlowMeter> flowmeter;
extern Ptr<LevelMeter> levelmeter;
extern Ptr<Display> display;
extern Ptr<MQTT> mqtt;
extern Preferences prefs;

void elements_setup();
void elements_loop();
void i2c_begin();

#endif
