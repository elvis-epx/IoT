#include <stdio.h>
#include <stdlib.h>

#include "LogDebug.h"
#include "Elements.h"
#include "Console.h"

void Log::d(const char *msg)
{
    console_println(msg);
    mqtt->pub_logdebug(msg);
}

static StrBuf buf;

void Log::d(const char *msg, const char *msg2)
{
    buf.reserve(strlen(msg) + 1 + strlen(msg2) + 1);
    sprintf(buf.hot_str(), "%s %s", msg, msg2);
    Log::d(buf.c_str());
}

void Log::d(const char *msg, int arg)
{
    buf.reserve(strlen(msg) + 15);
    sprintf(buf.hot_str(), "%s %d", msg, arg);
    Log::d(buf.c_str());
}

void Log::d(const char *msg, double arg)
{
    buf.reserve(strlen(msg) + 25);
    sprintf(buf.hot_str(), "%s %f", msg, arg);
    Log::d(buf.c_str());
}
