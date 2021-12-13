#include "H2OStateMachine.h"

void Initial::enter()
{
}

static bool initial_off()
{
	return true;
}

void On::enter()
{
}

void Off::enter()
{
}

H2OStateMachine::H2OStateMachine(): StateMachine()
{
	auto initial = Ptr<State>(new Initial());
	auto off = Ptr<State>(new Off());
	auto on = Ptr<State>(new On());

	initial->add(initial_off, "initial_off", off);

	add(initial);
	add(off);
	add(on);
}
