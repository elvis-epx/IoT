#ifndef __PUMP_H
#define __PUMP_H

#include "Timestamp.h"

class Pump
{
public:
	Pump();
	void on();
	void off();
	bool is_running() const;
	Timestamp running_since() const;
	static Timestamp flow_delay(); // in ms 

private:
	bool is_on;
	Timestamp since;
};

#endif
