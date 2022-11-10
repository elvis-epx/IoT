#include "Elements.h"
#include "LevelMeter.h"

LevelMeter::LevelMeter(const double levels[], double capacity):
    levels(levels), capacity(capacity)
{
    current_level = 100;
    next_eval = Timeout(1 * SECONDS);
    next_eval.advance();
    failure = false;
    first_bitmap = true;
}

bool LevelMeter::failure_detected() const
{
    return failure;
}

void LevelMeter::eval()
{
    if (next_eval.pending()) {
        return;
    }

    uint32_t bitmap = gpio->read_level_sensors();

    for (int i = 0; i < (DEBOUNCE_LENGTH - 1); ++i) {
        if (first_bitmap) {
            last_bitmaps[i + 1] = bitmap;
        }
        last_bitmaps[i] = last_bitmaps[i + 1];
    }
    last_bitmaps[DEBOUNCE_LENGTH - 1] = bitmap;
    first_bitmap = false;

    bool debounced = true;
    for (int i = 0; i < (DEBOUNCE_LENGTH - 1); ++i) {
        debounced = debounced && (last_bitmaps[i] == last_bitmaps[i + 1]);
    }
    if (debounced) {
        last_debounced_bitmap = last_bitmaps[0];
    }
    
    // display.debug("sensor bitmap", (int) last_debounced_bitmap);

    double new_level = 0;
    failure = false;

    int last_off = -1;

    for (int i = 0; levels[i] != 0; ++i) {
        // pull-up logic
        bool bit = !(last_debounced_bitmap & (0x01 << i));
        // display.debug("\tsw  ", i);
        // display.debug("\tbit ", bit ? "On" : "Off");

        if (bit) {
            // sensor is ON, level is at least here
            new_level = levels[i];

            if (last_off > -1) {
                // there was an OFF sensor below
                failure = true;
                // display.debug("sensor failure", last_off);
            }
        } else {
            // sensor is OFF
            last_off = i;
        }
    }


    // display.debug("level", current_level);
    // display.debug("failure", failure);

    if (new_level != current_level) {
        current_level = new_level;
        flowmeter->reset_volume();
    }
}

double LevelMeter::level_pct() const
{
    return current_level;
}

double LevelMeter::level_vol() const
{
    return current_level * capacity / 100;
}

/*
uint32_t LevelMeter::bitmap() const
{
    return last_debounced_bitmap;
}
*/
