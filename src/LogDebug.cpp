#include <stdio.h>
#ifndef UNDER_TEST
#include <Arduino.h>
#endif

#include "LogDebug.h"

void Log::d(const char *msg)
{
#ifdef UNDER_TEST
	printf("dbg %s\n", msg);
#else
	Serial.println(msg);
#endif
}

void Log::d(const char *msg, const char *msg2)
{
#ifdef UNDER_TEST
	printf("dbg %s %s\n", msg, msg2);
#else
	Serial.print(msg);
	Serial.print(" ");
	Serial.println(msg2);
#endif
}

void Log::d(const char *msg, int arg)
{
#ifdef UNDER_TEST
	printf("dbg %s %d\n", msg, arg);
#else
	Serial.println(msg);
	Serial.print(" ");
	Serial.println(arg);
#endif
}

void Log::d(const char *msg, double arg)
{
#ifdef UNDER_TEST
	printf("dbg %s %f\n", msg, arg);
#else
	Serial.print(msg);
	Serial.print(" ");
	Serial.println(arg);
#endif
}
