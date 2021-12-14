#include "H2OStateMachine.h"
#include "Plant.h"
#include <unistd.h>
#include <signal.h>

GPIO gpio;
Pump pump;
FlowMeter flowmeter(FLOWMETER_PULSE_RATE);
static const double level_sensors[] = LEVEL_SENSORS;
LevelMeter levelmeter(level_sensors, TANK_CAPACITY);
Display display;
H2OStateMachine sm;

static void sigusr1(int)
{
	gpio.pulse();
}

int main()
{
	signal(SIGUSR1, sigusr1);
	sm.start();

	while (true) {
		sleep(1);
		sm.eval();
		display.eval();
	}
}
