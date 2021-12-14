#include "Display.h"
#include "Plant.h"
#include <cstdio>

Display::Display()
{
	phase = 0;
	last_update = now();
	show("H2O Control", "by EPx");
}

void Display::eval()
{
	if ((now() - last_update) < 2000) {
		return;
	}
	
	last_update = now();
	++phase;
	if (phase > 3) {
		phase = 1;
	}

	char msg1[20];
	char msg2[20];

	sprintf(msg1, "State: %s", sm.cur_state_name());

	if (phase == 1) {
		sprintf(msg2, "Level: %.0f%%", levelmeter.level_pct());
	} else if (phase == 2) {
		sprintf(msg2, "Flow: %.1fL/s", flowmeter.rate());
	} else if (phase == 3) {
		sprintf(msg2, "Pumped: %.1fL", flowmeter.volume());
	}

	show(msg1, msg2);
}

void Display::show(const char *msg1, const char *msg2)
{
	printf("%s\n%s\n", msg1, msg2);
}

void Display::debug(const char *msg)
{
	printf("dbg %s\n", msg);
}

void Display::debug(const char *msg, int arg)
{
	printf("dbg %s %d\n", msg, arg);
}

void Display::debug(const char *msg, double arg)
{
	printf("dbg %s %f\n", msg, arg);
}
