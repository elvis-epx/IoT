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

private:
	void show(const char *, const char *);
	int phase;
	Timestamp last_update;
#ifndef UNDER_TEST
	Ptr<LCD_I2C> lcd;
#endif
};

#endif
