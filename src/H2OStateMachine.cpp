#include "H2OStateMachine.h"
#include "Plant.h"

void Initial::enter()
{
}

void On::enter()
{
	flowmeter.reset();
	pump.on();
}

void Off::enter()
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

H2OStateMachine::H2OStateMachine(): StateMachine()
{
	auto initial = Ptr<State>(new Initial());
	auto off = Ptr<State>(new Off());
	auto on = Ptr<State>(new On());

	initial->add(initial_off, "initial_off", off);
	off->add(low_level, "low_level", on);
	on->add(high_level, "high_level", off);

	add(initial);
	add(off);
	add(on);
}
