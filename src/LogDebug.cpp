#include <stdio.h>
#include <stdlib.h>
#ifndef UNDER_TEST
#include <Arduino.h>
#endif

#include "LogDebug.h"
#include "Elements.h"
#include "Console.h"

void Log::d(const char *msg)
{
    console_println(msg);
    mqtt->pub_logdebug(msg);
}

void Log::d(const char *msg, const char *msg2)
{
    char *s = (char*) malloc(strlen(msg) + 1 + strlen(msg2) + 1);
    sprintf(s, "%s %s", msg, msg2);
    Log::d(s);
    free(s);
}

void Log::d(const char *msg, int arg)
{
    char *s = (char*) malloc(strlen(msg) + 15);
    sprintf(s, "%s %d", msg, arg);
    Log::d(s);
    free(s);
}

void Log::d(const char *msg, double arg)
{
    char *s = (char*) malloc(strlen(msg) + 25);
    sprintf(s, "%s %f", msg, arg);
    Log::d(s);
    free(s);
}
