#ifndef UNDER_TEST

#include <Arduino.h>
#include <stdlib.h>

uint32_t _arduino_millis()
{
    return millis();
}

void arduino_restart() {
    ESP.restart();
}

void arduino_pinmode(int a, int b) {
    pinMode(a, b);
}

void arduino_digitalwrite(int a, bool b) {
    digitalWrite(a, b);
}

#else

#include <sys/time.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <iostream>
#include <fstream>

// Emulation of millis() and random()

static struct timeval tm_first;
int64_t uptime_advance = 0;
static bool virgin = true;

static void init_things()
{
    virgin = false;
    gettimeofday(&tm_first, 0);
    srandom(tm_first.tv_sec + tm_first.tv_usec);
}

uint32_t _arduino_millis()
{
    if (virgin) init_things();
    struct timeval tm;
    gettimeofday(&tm, 0);
    int64_t now_us   = tm.tv_sec * 1000000LL + uptime_advance * 1000000LL + tm.tv_usec;
    int64_t start_us = tm_first.tv_sec * 1000000LL + tm_first.tv_usec;
    // uptime in ms
    int64_t uptime_ms = (now_us - start_us) / 1000 + 1;
    return (uint32_t) (uptime_ms & 0xffffffffULL);
}

void arduino_restart() {
    // exit(0); // do not exit actually due to some Valgrind false positives
}

void arduino_pinmode(int, int) {}

void arduino_digitalwrite(int pin, bool state)
{
    char fname[40];
    sprintf(fname, "gpio%d.sim", pin);
    std::ofstream f;
    f.open(fname);
    f << (state ? 1 : 0);
    f.close();
}

#endif
