#include "H2OStateMachine.h"
#include "Elements.h"
#include "Constants.h"

void Initial::enter()
{
}

void On::enter()
{
	pump->on(); // resets flow meter if was off
}

void ManualOn::enter()
{
	pump->on(); // resets flow meter if was off
}

void Off::enter()
{
	pump->off();
}

void HisteresisOff::enter()
{
	pump->off();
}

void ManualOff::enter()
{
	pump->off();
}

void FlowFailure::enter()
{
	pump->off();
}

void LowFlowShort::enter()
{
	pump->off();
}

void LowFlowLong::enter()
{
	pump->off();
}

void PumpTimeout::enter()
{
	pump->off();
}

void LevelFailure::enter()
{
	pump->off();
}

static bool initial_off()
{
	return true;
}

static bool low_level()
{
	// keep this idiom so coverage tools can find out whether a
	// transition happened
	if (levelmeter->level_pct() < PUMP_THRESHOLD) {
		return true;
	}
	return false;
}

static bool high_level()
{
	if (levelmeter->level_pct() >= 100) {
		return true;
	}
	return false;
}

static bool pump_rest()
{
	if ((now() - sm->last_movement()) > (5 * MINUTES)) {
		return true;
	}
	return false;
}

static bool lvlf_recover()
{
	if ((now() - sm->last_movement()) > (12 * 60 * MINUTES)) {
		return true;
	}
	return false;
}

static bool lfl_recover()
{
	if ((now() - sm->last_movement()) > (12 * 60 * MINUTES)) {
		return true;
	}
	return false;
}

static bool pto_recover()
{
	if ((now() - sm->last_movement()) > (6 * 60 * MINUTES)) {
		return true;
	}
	return false;
}

static bool lfs_recover()
{
	if ((now() - sm->last_movement()) > (2 * 60 * MINUTES)) {
		return true;
	}
	return false;
}

static bool manual_on_sw_1()
{
	if (!(gpio->read_switches() & 0x01)) {
		return true;
	}
	return false;
}

static bool manual_on_sw_0()
{
	if (!manual_on_sw_1()) {
		return true;
	}
	return false;
}

static bool manual_off_sw_1()
{
	// pull-up logic
	if (!(gpio->read_switches() & 0x02)) {
		return true;
	}
	return false;
}

static bool manual_off_sw_0()
{
	if (!manual_off_sw_1()) {
		return true;
	}
	return false;
}

static bool detect_flow_fail()
{
	if ((now() - flowmeter->last_movement()) < (30 * SECONDS)) {
		return false;
	}

	Timestamp runtime = now() - pump->running_since();
	if (runtime < (2 * pump->flow_delay())) {
		// might be filling pipe between pump and flow meter
		return false;
	}

	return true;
}

static bool detect_low_flow_s()
{
	if (flowmeter->rate(FLOWRATE_SHORT) == -1) {
		// not measured yet
		return false;
	}

	Timestamp runtime = now() - pump->running_since();
	if (runtime < (2 * pump->flow_delay())) {
		// might be filling pipe between pump and flow meter
		return false;
	}

	if (flowmeter->rate(FLOWRATE_SHORT) < (ESTIMATED_PUMP_FLOWRATE / 4)) {
		// less than 25% expected flow
		return true;
	}

	return false;
}

static bool detect_low_flow_l()
{
	if (flowmeter->rate(FLOWRATE_LONG) == -1) {
		// not measured yet
		return false;
	}

	Timestamp runtime = now() - pump->running_since();
	if (runtime < (2 * pump->flow_delay())) {
		// might be filling pipe between pump and flow meter
		return false;
	}

	if (flowmeter->rate(FLOWRATE_LONG) < (ESTIMATED_PUMP_FLOWRATE / 3)) {
		// less than 33% expected flow
		return true;
	}

	return false;
}

static bool pump_timeout()
{
	Timestamp runtime = now() - pump->running_since();
	Timestamp fillup_time = (TANK_CAPACITY / ESTIMATED_PUMP_FLOWRATE) * MINUTES;

	if (runtime > (fillup_time * 2)) {
		return true;
	}
	return false;
}

static bool detect_level_fail()
{
	// This test assumes level changes in discrete steps.
	// If level meter was analog/continuous, a different strategy would
	// have to be implemented

	// volume between two level sensors
	double dvolume = levelmeter->next_level_liters() - levelmeter->level_liters();
	// pumped volume since last level change
	double pumped = flowmeter->volume();

	if (pumped > (2 * dvolume)) {
		return true;
	}
	return false;
}

H2OStateMachine::H2OStateMachine(): StateMachine()
{
	auto initial = Ptr<State>(new Initial());
	auto off = Ptr<State>(new Off());
	auto off_rest = Ptr<State>(new HisteresisOff());
	auto manual_off = Ptr<State>(new ManualOff());
	auto on = Ptr<State>(new On());
	auto manual_on = Ptr<State>(new ManualOn());
	auto flow_fail = Ptr<State>(new FlowFailure());
	auto lowflow_short = Ptr<State>(new LowFlowShort());
	auto lowflow_long = Ptr<State>(new LowFlowLong());
	auto pumptimeout = Ptr<State>(new PumpTimeout());
	auto level_fail = Ptr<State>(new LevelFailure());

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
