#ifndef __ELEMENTS_H
#define __ELEMENTS_H

#include <Preferences.h>
#include "Pointer.h"
#include "Sensor.h"
#include "MQTT.h"

extern Ptr<Sensor> sensor;
extern Ptr<MQTT> mqtt;
extern Preferences prefs;

void elements_setup();
void elements_loop();

#endif
