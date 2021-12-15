#include <cstdio>
#ifndef UNDER_TEST
#include <LCD_I2C.h>
#endif

#include "Display.h"
#include "Plant.h"

Display::Display()
{
#ifndef UNDER_TEST
	lcd = Ptr<LCD_I2C>(new LCD_I2C(0x3f, 16, 2));
	lcd.begin();
	// call with False in case there are other I2C devices
	// that call Wire.begin() first
	lcd.backlight();
#endif
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
	if (phase > 4) {
		phase = 1;
	}

	char msg1[20];
	char msg2[20];

	sprintf(msg1, "%s", sm.cur_state_name());

	if (phase == 1) {
		sprintf(msg2, "Level: %.0f%%", levelmeter.level_pct());
	} else if (phase == 2) {
		double rate = flowmeter.rate(FLOWRATE_INSTANT);
		if (rate >= 0) {
			sprintf(msg2, "Flow: %.1fL/min", flowmeter.rate(FLOWRATE_INSTANT));
		} else {
			sprintf(msg2, "Flow: unknown");
		}
	} else if (phase == 3) {
		sprintf(msg2, "Pumped: %.1fL", flowmeter.volume());
	} else if (phase == 4) {
		if (levelmeter.failure_detected()) {
			// FIXME report via MQTT 
			sprintf(msg2, "Err lvl %d", levelmeter.bitmap());
		} else {
			sprintf(msg2, "No errors");
		}
	}

	show(msg1, msg2);
}

void Display::show(const char *msg1, const char *msg2)
{
#ifdef UNDER_TEST
	printf("================\n%s\n%s\n", msg1, msg2);
#else
	lcd.clear();
	lcd.setCursor(0, 0);
	lcd.print(msg1);
	lcd.setCursor(0, 1);
	lcd.print(msg2);
#endif
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

void Display::debug(const char *msg, const char *msg2)
{
	printf("dbg %s %s\n", msg, msg2);
}
