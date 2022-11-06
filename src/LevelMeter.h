#ifndef __LEVELMETER_H
#define __LEVELMETER_H

#include "Timer.h"

#define DEBOUNCE_LENGTH 4

class LevelMeter
{
public:
    // Levels, in % of each of the sensors
    // must be in ascending order
    // must terminate with 100, 0
    LevelMeter(const double levels[], double capacity);

    void eval();

    double level_pct() const; // in %
    double level_liters() const; // in liters
    double next_level_liters() const; // in liters
    bool failure_detected() const;
    uint32_t bitmap() const;

private:

    Timeout next_eval;
    const double *levels;
    double current_level;
    double capacity; // estimated tank capacity in liters

    bool failure;
    uint32_t last_debounced_bitmap;
    uint32_t last_bitmaps[DEBOUNCE_LENGTH];
    bool first_bitmap;
};

#endif
