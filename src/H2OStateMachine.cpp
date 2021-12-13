#include "H2OStateMachine.h"

H2OStateMachine::H2OStateMachine(): StateMachine()
{
	auto initial = Ptr<State>(new Initial());
	auto off = Ptr<State>(new Off());
	auto on = Ptr<State>(new On());

	add(initial);
	add(off);
	add(on);
	start();
}
