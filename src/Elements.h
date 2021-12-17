#ifndef __ELEMENTS_H
#define __ELEMENTS_H

#include "Pointer.h"
#include "Pump.h"
#include "FlowMeter.h"
#include "LevelMeter.h"
#include "GPIO.h"
#include "Display.h"
#include "H2OStateMachine.h"

extern Ptr<GPIO> gpio;
extern Ptr<Pump> pump;
extern Ptr<FlowMeter> flowmeter;
extern Ptr<LevelMeter> levelmeter;
extern Ptr<Display> display;
extern Ptr<H2OStateMachine> sm;

#endif
