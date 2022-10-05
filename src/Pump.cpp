#include "Pump.h"
#include "Elements.h"
#include "Constants.h"
#include "LogDebug.h"

Pump::Pump()
{
    since = now();
    is_on = false;
}

void Pump::on()
{
    if (! is_on) {
        Log::d("pump on");
        since = now();
        is_on = true;
        flowmeter->reset_all();
        gpio->write_pump(true);
    }
}

void Pump::off()
{
    if (is_on) {
        Log::d("pump off");
        since = now();
        is_on = false;
        gpio->write_pump(false);
    }
}

bool Pump::is_running() const
{
    return is_on;
}

Timestmp Pump::running_since() const
{
    return since;
}

Timestmp Pump::flow_delay()
{
    double pipe_area_mm2 = (PIPE_DIAMETER * PIPE_DIAMETER / 4.0) * 3.142;
    double pipe_area_cm2 = pipe_area_mm2 / 100;
    double pipe_length_cm = PIPE_LENGTH * 100.0;
    double pipe_volume_mL = pipe_area_cm2 * pipe_length_cm;
    double pipe_volume_L = pipe_volume_mL / 1000.0;

    return (pipe_volume_L / ESTIMATED_PUMP_FLOWRATE) * MINUTES;
}
