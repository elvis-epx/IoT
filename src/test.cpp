#include "H2OStateMachine.h"
#include "Plant.h"
#include <unistd.h>

Pump pump;
FlowMeter flowmeter(FLOWMETER_PULSE_RATE);
static const double level_sensors[] = LEVEL_SENSORS;
LevelMeter levelmeter(level_sensors, TANK_CAPACITY);

int main()
{
	H2OStateMachine sm;
	sm.start();
	for (int i = 0; i < 100; ++i) {
		sleep(1);
		sm.eval();
	}
}
