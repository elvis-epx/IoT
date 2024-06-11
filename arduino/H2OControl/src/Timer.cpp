/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2020 PU5EPX
 */

#include "ArduinoBridge.h"
#include "Timer.h"
#ifdef UNDER_TEST
#include <stdlib.h>
#endif

static uint32_t epoch = 0;
static uint32_t last_millis = 0;

Timestmp now()
{
    uint32_t m = _arduino_millis();
    if ((m < last_millis) && (last_millis - m) > 0x10000000) {
        // wrapped around
        epoch += 1;
    }
    last_millis = m;
    return (((int64_t) epoch) << 32) + m;
}

static const int INVALID = 0;
static const int ACTIVE = 1;
static const int STOPPED = 2;

Timeout::Timeout()
{
    state = INVALID;
}

Cronometer::Cronometer()
{
    restart();
}

Timeout::Timeout(Timestmp pdelta)
{
    state = STOPPED;
    delta = pdelta;
    restart();
}

void Timeout::restart()
{
    if (state == INVALID) {
#ifdef UNDER_TEST
        abort();
#endif
        return;
    }
    target = now() + delta;
    state = ACTIVE;
}

void Cronometer::restart()
{
    started = now();
}

void Timeout::advance()
{
    if (state == INVALID) {
#ifdef UNDER_TEST
        abort();
#endif
        return;
    }
    target = now();
}

bool Timeout::pending()
{
    if (state == INVALID) {
#ifdef UNDER_TEST
        abort();
#endif
        return true;
    }
    if (state == STOPPED) {
#ifdef UNDER_TEST
        abort();
#endif
        return true;
    }
    if (now() < target) {
        return true;
    }
    restart();
    return false;
}

void Timeout::stop()
{
    if (state == INVALID) {
#ifdef UNDER_TEST
        abort();
#endif
        return;
    }
    state = STOPPED;
}

Timestmp Cronometer::elapsed() const
{
    return now() - started;
}
