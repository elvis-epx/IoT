#ifndef __DISPLAY_H
#define __DISPLAY_H

#include "Timestamp.h"
#include "Pointer.h"

#ifndef UNDER_TEST
class LCD_I2C;
#endif

class Display
{
public:
	Display();
	void eval();
	void debug(const char *);
	void debug(const char *, const char *);
	void debug(const char *, int);
	void debug(const char *, double);
	static void millis_to_hms(int64_t t, char *target);

private:
	void show(char **);
	int row2_phase;
	int row3_phase;
	Timestamp last_update;
	Timestamp last_row2_update;
	Timestamp last_row3_update;
#ifndef UNDER_TEST
	Ptr<LCD_I2C> lcd;
#endif
};

#endif
