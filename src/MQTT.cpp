#include "MQTT.h"

MQTT::MQTT()
{
}

MQTT::~MQTT()
{
}

bool MQTT::override_on_state() const
{
	return false;
}


bool MQTT::override_off_state() const
{
	return false;
}
