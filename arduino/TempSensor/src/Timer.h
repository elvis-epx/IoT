/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#ifndef __TIMER_H
#define __TIMER_H

#include "stdint.h"

typedef int64_t Timestmp;

Timestmp now();
#define MILISSECONDS 1
#define SECONDS 1000
#define MINUTES 60000

class Timeout {
public:
    Timeout();
    Timeout(Timestmp);
    void restart();
    void advance();
    bool pending();
    void stop();
private:
    Timestmp target;
    Timestmp delta;
    int state;
};

class Cronometer {
public:
    Cronometer();
    void restart();
    Timestmp elapsed() const;
private:
    Timestmp started;
};

#endif
