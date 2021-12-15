#include "H2OStateMachine.h"
#include "Plant.h"

void Initial::enter()
{
}

void On::enter()
{
	pump.on(); // resets flow meter if was off
}

void ManualOn::enter()
{
	pump.on(); // resets flow meter if was off
}

void Off::enter()
{
	pump.off();
}

void HisteresisOff::enter()
{
	pump.off();
}

void ManualOff::enter()
{
	pump.off();
}

void FlowFailure::enter()
{
	pump.off();
}

void LevelFailure::enter()
{
	pump.off();
}

static bool initial_off()
{
	return true;
}

static bool low_level()
{
	return levelmeter.level_pct() < LOWLEVEL_THRESHOLD;
}

static bool high_level()
{
	return levelmeter.level_pct() >= 100;
}

static bool timeout_5min()
{
	return sm.since_last_transition() > (5 * MINUTES);
}

static bool timeout_12h()
{
	return sm.since_last_transition() > (12 * 60 * MINUTES);
}

static bool manual_on_sw_1()
{
	return gpio.read_switches() & 0x01;
}

static bool manual_on_sw_0()
{
	return !manual_on_sw_1();
}

static bool manual_off_sw_1()
{
	return gpio.read_switches() & 0x02;
}

static bool manual_off_sw_0()
{
	return !manual_off_sw_1();
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

	on->add(manual_on_sw_1,    "manual_off_sw_1",   off);
	on->add(manual_on_sw_1,    "manual_on_sw_1",    manual_on);
	on->add(high_level,        "high_level",        off_rest);
	on->add(detect_flow_fail,  "detect_flow_fail",  flow_fail);
	on->add(detect_level_fail, "detect_level_fail", level_fail);
	add(on);

	off_rest->add(manual_off_sw_1, "manual_off_sw_1", off);
	off_rest->add(manual_on_sw_1,  "manual_on_sw_1",  off);
	off_rest->add(timeout_5min,    "timeout_5min",    off);
	add(off_rest);

	flow_fail->add(manual_off_sw_1, "manual_off_sw_1", off);
	flow_fail->add(manual_on_sw_1,  "manual_on_sw_1",  off);
	add(flow_fail);

	level_fail->add(manual_off_sw_1, "manual_off_sw_1", off);
	level_fail->add(manual_on_sw_1,  "manual_on_sw_1",  off);
	level_fail->add(timeout_12h,     "timeout_12h",     off);
	add(level_fail);
}
