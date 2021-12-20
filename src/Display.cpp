#include "stdio.h"
#ifndef UNDER_TEST
#include <LCD_I2C.h>
#endif

#include "Display.h"
#include "Elements.h"
#include "Constants.h"

Display::Display()
{
	row2_phase = 1;
	row3_phase = 1;
	last_update = last_row2_update = last_row3_update = now();

#ifndef UNDER_TEST
	lcd = Ptr<LCD_I2C>(new LCD_I2C(0x3f, 16, 2));
	lcd->begin();
	// call begin() with False in case there are other I2C devices
	// that call Wire.begin() first
	lcd->backlight();
#endif

	const char *msg[] = {"", "", "", ""};
	show((char**) msg);
}

void Display::millis_to_hms(int64_t t, char *target)
{
	if (t < 0) {
		sprintf(target, "...");
		return;
	}
	t /= 1000;
	int32_t s = t % 60;
	t -= s;
	t /= 60;
	int32_t m = t % 60;
	t -= m;
	t /= 60;
	int32_t h = t % 24;
	t -= h;
	t /= 24;
	int32_t d = t;

	if (d > 0) {
		sprintf(target, "Uptime %d:%02d:%02d:%02d", d, h, m, s);
	} else if (h > 0) {
		sprintf(target, "Uptime %d:%02d:%02d", h, m, s);
	} else {
		sprintf(target, "Uptime %d:%02d", m, s);
	}
}

void Display::eval()
{
	Timestamp Now = now();
	if ((Now - last_update) < 1000) {
		return;
	}
	last_update = Now;

	if ((Now - last_row2_update) >= 5000) {
		++row2_phase;
		if (row2_phase > 3) {
			row2_phase = 1;
		}
		last_row2_update = Now;
	}

	if ((Now - last_row3_update) >= 5000) {
		++row3_phase;
		if (row3_phase > 3) {
			row3_phase = 1;
		}
		last_row3_update = Now;
	}

	char msg0[30];
	char msg1[30];
	char msg2[30];
	char msg3[30];
	char *msg[4];
	msg[0] = msg0; msg[1] = msg1; msg[2] = msg2; msg[3] = msg3;

	sprintf(msg[0], "%s", sm->cur_state_name());

	// FIXME report level error via MQTT 
	const char *err = levelmeter->failure_detected() ? "E " : "";
	sprintf(msg[1], "%s%.0f%% + %.0fL", err, levelmeter->level_pct(), flowmeter->volume());

	if (row2_phase == 1) {
		double rate = flowmeter->rate(FLOWRATE_LONG);
		if (rate >= 0) {
			sprintf(msg[2], "%.1fL/min x 30m", rate);
		} else {
			row2_phase = 2;
		}
	}
	if (row2_phase == 2) {
		double rate = flowmeter->rate(FLOWRATE_SHORT);
		if (rate >= 0) {
			sprintf(msg[2], "%.1fL/min x 2m", rate);
		} else {
			row2_phase = 3;
		}
	}
	if (row2_phase == 3) {
		double rate = flowmeter->rate(FLOWRATE_INSTANT);
		if (rate >= 0) {
			sprintf(msg[2], "%.1fL/min x 10s", rate);
		} else {
			sprintf(msg[2], "...");
		}
	}

	if (row3_phase == 1) {
		millis_to_hms(Now, msg[3]);
	}
	if (row3_phase == 2) {
		if (pump->is_running()) {
			double volume = flowmeter->volume();
			double exp_volume = flowmeter->expected_volume();
		 	if (exp_volume > 0) {
				sprintf(msg[3], "Efficiency %.0f%%",
					100 * volume / exp_volume);
			} else {
				sprintf(msg[3], "Efficiency ...");
			}
		} else {
			row3_phase = 3;
		}
	}
	if (row3_phase == 3) {
		sprintf(msg[3], "%s", "H2O Control (c) EPx");
	}

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
	lcd->print(msg[0]);
	lcd->setCursor(0, 1);
	lcd->print(msg[1]);
	lcd->setCursor(0, 2);
	lcd->print(msg[2]);
	lcd->setCursor(0, 3);
	lcd->print(msg[3]);
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

