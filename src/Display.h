#ifndef __DISPLAY_H
#define __DISPLAY_H

#include "Timestamp.h"

class Display
{
public:
	Display();
	void eval();
	void debug(const char *);
	void debug(const char *, int);
	void debug(const char *, double);

private:
	void show(const char *, const char *);
	int phase;
	Timestamp last_update;
};

#endif
