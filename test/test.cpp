#include <unistd.h>
#include <stdio.h>
#include <iostream>
#include <fstream>
#include <assert.h>

#include "Elements.h"
#include "Constants.h"
#include "LogDebug.h"
#include "Console.h"

// to simulate accelerated time
extern int64_t uptime_advance;

int main()
{
    elements_setup();

    bool running = true;
    while (running) {
        elements_loop();
        usleep(10000);

        std::ofstream g;
        g.open("state.sim");
        g << sm->cur_state_name() << std::endl;
        g << levelmeter->level_pct() << std::endl;
        g << levelmeter->level_liters() << std::endl;
        g << flowmeter->rate(FLOWRATE_INSTANT) << std::endl;
        g << flowmeter->rate(FLOWRATE_SHORT) << std::endl;
        g << flowmeter->rate(FLOWRATE_LONG) << std::endl;
        if (levelmeter->failure_detected()) {
            g << "E";
        }
        g << std::endl;
        g.close();

        std::ifstream f;
        f.open("quit.sim");
        running = !f.is_open();
        f.close();

        f.open("timeadvance.sim");
        if (f.is_open()) {
            int64_t offset = 0;
            f >> offset;
            uptime_advance += offset;
            std::remove("timeadvance.sim");
        }
        f.close();
    }

    // test invalid flow rate argument
    assert(flowmeter->rate(12345) == -2);
    Log::d("int", 1);
    Log::d("double", 1.0);
    Log::d("string", "bla");
    assert(strcmp(mqtt->mqtt_id(), "H2OControl") == 0);
    assert(!mqtt->pub_by_topic("NoSuchTopic"));

    char tmp[40];
    Display::millis_to_hms(-1, tmp);
    assert(strcmp(tmp, "...") == 0);
    Display::millis_to_hms(86401 * 1000, tmp);
    assert(strcmp(tmp, "Uptime 1:00:00:01") == 0);
    Display::millis_to_hms(3602 * 1000, tmp);
    assert(strcmp(tmp, "Uptime 1:00:02") == 0);

    std::remove("quit.sim");
}
