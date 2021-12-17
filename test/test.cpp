#include <unistd.h>
#include <stdio.h>
#include <iostream>
#include <fstream>

#include "Elements.h"
#include "Constants.h"

static const double level_sensors[] = LEVEL_SENSORS;
static const uint32_t flow_rates[] = FLOWRATES;

Ptr<GPIO> gpio;
Ptr<Pump> pump;
Ptr<FlowMeter> flowmeter;
Ptr<LevelMeter> levelmeter;
Ptr<Display> display;
Ptr<H2OStateMachine> sm;

int main()
{
	gpio = Ptr<GPIO>(new GPIO());
	pump = Ptr<Pump>(new Pump());
	flowmeter = Ptr<FlowMeter>(new FlowMeter(FLOWMETER_PULSE_RATE, flow_rates));
	levelmeter = Ptr<LevelMeter>(new LevelMeter(level_sensors, TANK_CAPACITY));
	display = Ptr<Display>(new Display());
	sm = Ptr<H2OStateMachine>(new H2OStateMachine());

	sm->start();

	bool running = true;
	while (running) {
		gpio->eval();
		flowmeter->eval();
		levelmeter->eval();
		sm->eval();
		display->eval();
		usleep(100000);

		std::ifstream f;
		f.open("quit.txt");
		running = !f.is_open();
		f.close();
	}

	std::remove("quit.txt");
}
