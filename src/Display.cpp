#include "stdio.h"
#ifndef UNDER_TEST
#include <LCD_I2C.h>
#endif

#include "Display.h"
#include "Plant.h"

Display::Display()
{
	phase = 0;
	last_update = now();

#ifndef UNDER_TEST
	lcd = Ptr<LCD_I2C>(new LCD_I2C(0x3f, 16, 2));
	lcd->begin();
	// call with False in case there are other I2C devices
	// that call Wire.begin() first
	lcd->backlight();
#endif

	const char *msg[] = {"H2O Control", "", "(c) 2021 EPx", ""};
	show((char**) msg);
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

	char msg0[30];
	char msg1[30];
	char msg2[30];
	char msg3[30];
	char *msg[4];
	msg[0] = msg0;
	msg[1] = msg1;
	msg[2] = msg2;
	msg[3] = msg3;

	sprintf(msg[0], "%s", sm->cur_state_name());

	// FIXME show uptime
	// FIXME show context-sensitive messages
	// FIXME show messages with early warnings of error conditions (low flow, etc.)
	// FIXME report level error via MQTT 

	const char *err = levelmeter->failure_detected() ? "E " : "";
	sprintf(msg[1], "%s%.0f%% + %.1fL", err, levelmeter->level_pct(), flowmeter->volume());

	if (phase == 3) {
		double rate = flowmeter->rate(FLOWRATE_LONG);
		if (rate >= 0) {
			sprintf(msg[2], "%.1fL/min x 30m", flowmeter->rate(FLOWRATE_INSTANT));
		} else {
			phase = 2;
		}
	}
	if (phase == 2) {
		double rate = flowmeter->rate(FLOWRATE_SHORT);
		if (rate >= 0) {
			sprintf(msg[2], "%.1fL/min x 2m", flowmeter->rate(FLOWRATE_INSTANT));
		} else {
			phase = 1;
		}
	}
	if (phase == 1) {
		double rate = flowmeter->rate(FLOWRATE_INSTANT);
		if (rate >= 0) {
			sprintf(msg[2], "%.1fL/min x 10s", flowmeter->rate(FLOWRATE_INSTANT));
		} else {
			sprintf(msg[2], "...");
		}
	}
	// FIXME warnings, other things in msg3
	sprintf(msg[3], "%s", "");

	show(msg);
}

void Display::show(char **msg)
{
#ifdef UNDER_TEST
	printf("\033[s");
	printf("\033[44m");
	printf("\033[97m");
	printf("\033[1;60H");
	printf("  %-20s  ", "");
	printf("\033[2;60H");
	printf("  %-20s  ", msg[0]);
	printf("\033[3;60H");
	printf("  %-20s  ", msg[1]);
	printf("\033[4;60H");
	printf("  %-20s  ", msg[2]);
	printf("\033[5;60H");
	printf("  %-20s  ", msg[3]);
	printf("\033[6;60H");
	printf("  %-20s  ", "");
	printf("\033[u");
	fflush(stdout);
#else
	lcd->clear();
	lcd->setCursor(0, 0);
	lcd->print(msg1);
	lcd->setCursor(0, 1);
	lcd->print(msg2);
#endif
}

void Display::debug(const char *msg)
{
#ifdef UNDER_TEST
	printf("dbg %s\n", msg);
#else
	Serial.println(msg);
#endif
}

void Display::debug(const char *msg, int arg)
{
#ifdef UNDER_TEST
	printf("dbg %s %d\n", msg, arg);
#else
	Serial.println(msg);
	Serial.print(" ");
	Serial.println(arg);
#endif
}

void Display::debug(const char *msg, double arg)
{
#ifdef UNDER_TEST
	printf("dbg %s %f\n", msg, arg);
#else
	Serial.print(msg);
	Serial.print(" ");
	Serial.println(arg);
#endif
}

void Display::debug(const char *msg, const char *msg2)
{
#ifdef UNDER_TEST
	printf("dbg %s %s\n", msg, msg2);
#else
	Serial.print(msg);
	Serial.print(" ");
	Serial.println(msg2);
#endif
}
