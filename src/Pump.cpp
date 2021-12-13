#include "Pump.h"

Pump::Pump()
{
	since = now();
	is_on = false;
}

void Pump::on()
{
	if (! is_on) {
		since = now();
		is_on = true;
	}
}

void Pump::off()
{
	if (is_on) {
		since = now();
		is_on = false;
	}
}

bool Pump::is_running() const
{
	return is_on;
}

Timestamp Pump::running_time() const
{
	return now() - since;
}
