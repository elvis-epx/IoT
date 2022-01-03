#include <unistd.h>
#include <stdio.h>
#include <iostream>
#include <fstream>
#include <assert.h>

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
Ptr<MQTT> mqtt;

// to simulate accelerated time
extern int64_t uptime_advance;

int main()
{
	gpio = Ptr<GPIO>(new GPIO());
	pump = Ptr<Pump>(new Pump());
	flowmeter = Ptr<FlowMeter>(new FlowMeter(FLOWMETER_PULSE_RATE, flow_rates));
	levelmeter = Ptr<LevelMeter>(new LevelMeter(level_sensors, TANK_CAPACITY));
	display = Ptr<Display>(new Display());
	sm = Ptr<H2OStateMachine>(new H2OStateMachine());
	mqtt = Ptr<MQTT>(new MQTT());

	sm->start();

	bool running = true;
	while (running) {
		gpio->eval();
		flowmeter->eval();
		levelmeter->eval();
		sm->eval();
		display->eval();
		mqtt->eval();
		usleep(100000);

		std::ofstream g;
		g.open("state.sim");
		g << sm->cur_state_name() << std::endl;
		g << levelmeter->level_pct() << std::endl;
		g << levelmeter->level_liters() << std::endl;
		g << flowmeter->rate(FLOWRATE_INSTANT) << std::endl;
		g << flowmeter->rate(FLOWRATE_SHORT) << std::endl;
		g << flowmeter->rate(FLOWRATE_LONG) << std::endl;
		if (levelmeter->failure_detected()) {
			g << "E";
		}
		g << std::endl;
		g.close();

		std::ifstream f;
		f.open("quit.sim");
		running = !f.is_open();
		f.close();

		f.open("timeadvance.sim");
		if (f.is_open()) {
			int64_t offset = 0;
			f >> offset;
			uptime_advance += offset;
			std::remove("timeadvance.sim");
		}
		f.close();
	}

	// test invalid flow rate argument
	assert(flowmeter->rate(12345) == -2);
	display->debug("int", 1);
	display->debug("double", 1.0);
	display->debug("string", "bla");

	char tmp[40];
	Display::millis_to_hms(-1, tmp);
	assert(strcmp(tmp, "...") == 0);
	Display::millis_to_hms(86401 * 1000, tmp);
	assert(strcmp(tmp, "Uptime 1:00:00:01") == 0);
	Display::millis_to_hms(3602 * 1000, tmp);
	assert(strcmp(tmp, "Uptime 1:00:02") == 0);

	std::remove("quit.sim");
}
