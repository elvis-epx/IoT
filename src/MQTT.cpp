#include "MQTT.h"

#ifdef UNDER_TEST

#include <iostream>
#include <fstream>

#else
#endif

MQTT::MQTT()
{
	override_on_switch = false;
	override_off_switch = false;
}

MQTT::~MQTT()
{
}

bool MQTT::override_on_state() const
{
	return override_on_switch;
}


bool MQTT::override_off_state() const
{
	return override_off_switch;
}

void MQTT::eval()
{
#ifdef UNDER_TEST
	// simulate receiving MQTT commands
	std::ifstream f;
	int x = 0;
	f.open("mqtt.sim");
	if (f.is_open()) {
		f >> x;
		std::remove("mqtt.sim");
	}
	f.close();
	if (x == 1) {
		override_on_switch = true;
	} else if (x == 2) {
		override_on_switch = false;
	} else if (x == 3) {
		override_off_switch = true;
	} else if (x == 4) {
		override_off_switch = false;
	}
#else
#endif
}
