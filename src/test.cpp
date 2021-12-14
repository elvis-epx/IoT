#include "H2OStateMachine.h"
#include "Plant.h"
#include <unistd.h>
#include <signal.h>

GPIO gpio;
Pump pump;
FlowMeter flowmeter(FLOWMETER_PULSE_RATE);
static const double level_sensors[] = LEVEL_SENSORS;
LevelMeter levelmeter(level_sensors, TANK_CAPACITY);

static void sigusr1(int)
{
	gpio.pulse();
}

int main()
{
	signal(SIGUSR1, sigusr1);

	H2OStateMachine sm;
	sm.start();

	for (int i = 0; i < 100; ++i) {
		sleep(1);
		sm.eval();
	}
}
