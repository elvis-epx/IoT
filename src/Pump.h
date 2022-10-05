#ifndef __PUMP_H
#define __PUMP_H

#include "Timer.h"

class Pump
{
public:
    Pump();
    void on();
    void off();
    bool is_running() const;
    Timestmp running_since() const;
    static Timestmp flow_delay(); // in ms 

private:
    bool is_on;
    Timestmp since;
};

#endif
