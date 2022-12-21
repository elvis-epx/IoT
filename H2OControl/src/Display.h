#ifndef __DISPLAY_H
#define __DISPLAY_H

#include "Timer.h"
#include "Pointer.h"

class Display
{
public:
    Display();
    void eval();
    static void millis_to_hms(int64_t t, char *target);

private:
    void show(char **);
    int row2_phase;
    int row3_phase;
    Timeout next_update;
    Timeout next_row2_update;
    Timeout next_row3_update;
    bool ok;
};

#endif
