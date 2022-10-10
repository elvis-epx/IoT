#include "H2OStateMachine.h"
#include "Elements.h"
#include "Constants.h"

Initial::Initial(int i): State(i) {}

void Initial::enter() {}

On::On(int i): State(i) {}

void On::enter()
{
    pump->on(); // resets flow meter if was off
}

ManualOn::ManualOn(int i): State(i) {}

void ManualOn::enter()
{
    pump->on(); // resets flow meter if was off
}

Off::Off(int i): State(i) {}

void Off::enter()
{
    pump->off();
}

HisteresisOff::HisteresisOff(int i): State(i) {}

void HisteresisOff::enter()
{
    pump->off();
}

ManualOff::ManualOff(int i): State(i) {}

void ManualOff::enter()
{
    pump->off();
}

FlowFailure::FlowFailure(int i): State(i) {}

void FlowFailure::enter()
{
    pump->off();
}

LowFlowShort::LowFlowShort(int i): State(i) {}

void LowFlowShort::enter()
{
    pump->off();
}

LowFlowLong::LowFlowLong(int i): State(i) {}

void LowFlowLong::enter()
{
    pump->off();
}

PumpTimeout::PumpTimeout(int i): State(i) {}

void PumpTimeout::enter()
{
    pump->off();
}

LevelFailure::LevelFailure(int i): State(i) {}

void LevelFailure::enter()
{
    pump->off();
}

static bool initial_off(int)
{
    return true;
}

static bool low_level(int)
{
    // keep this idiom so coverage tools can find out whether a
    // transition happened
    if (levelmeter->level_pct() < PUMP_THRESHOLD) {
        return true;
    }
    return false;
}

static bool high_level(int)
{
    if (levelmeter->level_pct() >= 100) {
        return true;
    }
    return false;
}

static bool pump_rest(int)
{
    if (sm->last_movement().elapsed() > PUMP_REST_TIME) {
        return true;
    }
    return false;
}

static bool lvlf_recover(int)
{
    if (sm->last_movement().elapsed() > LEVEL_FAIL_RECOVERY) {
        return true;
    }
    return false;
}

static bool lfl_recover(int)
{
    if (sm->last_movement().elapsed() > LOWFLOW_LONG_RECOVERY) {
        return true;
    }
    return false;
}

static bool pto_recover(int)
{
    if (sm->last_movement().elapsed() > PUMP_TIMEOUT_RECOVERY) {
        return true;
    }
    return false;
}

static bool lfs_recover(int)
{
    if (sm->last_movement().elapsed() > LOWFLOW_SHORT_RECOVERY) {
        return true;
    }
    return false;
}

static bool manual_on_sw_1(int)
{
    if (mqtt->override_on_state()) {
        return true;
    }
    return false;
}

static bool manual_on_sw_0(int)
{
    if (!manual_on_sw_1(0)) {
        return true;
    }
    return false;
}

static bool manual_off_sw_1(int)
{
    if (mqtt->override_off_state()) {
        return true;
    }
    return false;
}

static bool manual_off_sw_0(int)
{
    if (!manual_off_sw_1(0)) {
        return true;
    }
    return false;
}

static bool detect_flow_fail(int)
{
    if (flowmeter->last_movement().elapsed() < MINIMUM_FLOW_LATENCY) {
        return false;
    }

    if (pump->running_time().elapsed() < (FLOW_DELAY_TOLERANCE * pump->flow_delay())) {
        // might be filling pipe between pump and flow meter
        return false;
    }

    return true;
}

static bool detect_low_flow_s(int)
{
    if (flowmeter->rate(FLOWRATE_SHORT) == -1) {
        // not measured yet
        return false;
    }

    if (pump->running_time().elapsed() < (FLOW_DELAY_TOLERANCE * pump->flow_delay())) {
        // might be filling pipe between pump and flow meter
        return false;
    }

    if (flowmeter->rate(FLOWRATE_SHORT) < (ESTIMATED_PUMP_FLOWRATE * LOWFLOW_SHORT_TOLERANCE)) {
        return true;
    }

    return false;
}

static bool detect_low_flow_l(int)
{
    if (pump->running_time().elapsed() < (FLOW_DELAY_TOLERANCE * pump->flow_delay())) {
        // might be filling pipe between pump and flow meter
        return false;
    }

    if (flowmeter->rate(FLOWRATE_LONG) == -1) {
        // not measured yet
        return false;
    }

    if (flowmeter->rate(FLOWRATE_LONG) < (ESTIMATED_PUMP_FLOWRATE * LOWFLOW_LONG_TOLERANCE)) {
        return true;
    }

    return false;
}

static bool pump_timeout(int)
{
    Timestmp fillup_time = (TANK_CAPACITY / ESTIMATED_PUMP_FLOWRATE) * MINUTES;

    if (pump->running_time().elapsed() > (fillup_time * PUMP_TIMEOUT_TOLERANCE)) {
        return true;
    }
    return false;
}

static bool detect_level_fail(int)
{
    // This test assumes level changes in discrete steps.
    // If level meter was analog/continuous, a different strategy would
    // have to be implemented

    // volume between two level sensors
    double dvolume = levelmeter->next_level_liters() - levelmeter->level_liters();
    // pumped volume since last level change
    double pumped = flowmeter->volume();

    if (pumped > (LEVEL_FAIL_TOLERANCE * dvolume)) {
        return true;
    }
    return false;
}

H2OStateMachine::H2OStateMachine(): StateMachine(0)
{
    auto initial = Ptr<State>(new Initial(0));
    auto off = Ptr<State>(new Off(0));
    auto off_rest = Ptr<State>(new HisteresisOff(0));
    auto manual_off = Ptr<State>(new ManualOff(0));
    auto on = Ptr<State>(new On(0));
    auto manual_on = Ptr<State>(new ManualOn(0));
    auto flow_fail = Ptr<State>(new FlowFailure(0));
    auto lowflow_short = Ptr<State>(new LowFlowShort(0));
    auto lowflow_long = Ptr<State>(new LowFlowLong(0));
    auto pumptimeout = Ptr<State>(new PumpTimeout(0));
    auto level_fail = Ptr<State>(new LevelFailure(0));

    initial->add(initial_off, "initial_off", off);
    add(initial);

    off->add(manual_off_sw_1, "manual_off_sw_1", manual_off);
    off->add(manual_on_sw_1,  "manual_on_sw_1",  manual_on);
    off->add(low_level,       "low_level",       on);
    add(off);

    manual_off->add(manual_off_sw_0, "manual_off_sw_0", off);
    add(manual_off);

    manual_on->add(manual_on_sw_0,  "manual_on_sw_0",  off);
    manual_on->add(manual_off_sw_1, "manual_off_sw_1", off);
    add(manual_on);

    on->add(manual_off_sw_1,   "manual_off_sw_1",   off);
    on->add(manual_on_sw_1,    "manual_on_sw_1",    manual_on);
    on->add(high_level,        "high_level",        off_rest);
    on->add(detect_flow_fail,  "detect_flow_fail",  flow_fail);
    on->add(detect_level_fail, "detect_level_fail", level_fail);
    on->add(detect_low_flow_s, "detect_low_flow_s", lowflow_short);
    on->add(detect_low_flow_l, "detect_low_flow_l", lowflow_long);
    on->add(pump_timeout,      "pump_timeout",      pumptimeout);
    add(on);

    off_rest->add(manual_off_sw_1, "manual_off_sw_1", off);
    off_rest->add(manual_on_sw_1,  "manual_on_sw_1",  off);
    off_rest->add(pump_rest,       "pump_rest",       off);
    add(off_rest);

    flow_fail->add(manual_off_sw_1, "manual_off_sw_1", off);
    flow_fail->add(manual_on_sw_1,  "manual_on_sw_1",  off);
    add(flow_fail);

    level_fail->add(manual_off_sw_1, "manual_off_sw_1", off);
    level_fail->add(manual_on_sw_1,  "manual_on_sw_1",  off);
    level_fail->add(lvlf_recover,    "lvlf_recover",    off);
    add(level_fail);

    lowflow_short->add(manual_off_sw_1, "manual_off_sw_1", off);
    lowflow_short->add(manual_on_sw_1,  "manual_on_sw_1",  off);
    lowflow_short->add(lfs_recover,     "lfs_recover",     off);
    add(lowflow_short);

    lowflow_long->add(manual_off_sw_1, "manual_off_sw_1", off);
    lowflow_long->add(manual_on_sw_1,  "manual_on_sw_1",  off);
    lowflow_long->add(lfl_recover,     "lfl_recover",     off);
    add(lowflow_long);

    pumptimeout->add(manual_off_sw_1, "manual_off_sw_1", off);
    pumptimeout->add(manual_on_sw_1,  "manual_on_sw_1",  off);
    pumptimeout->add(pto_recover,     "pto_recover",     off);
    add(pumptimeout);
}

