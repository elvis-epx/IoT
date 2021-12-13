#include "StateMachine.h"

void State::add(Ptr<Transition> trans)
{
	transitions.push_back(trans);
}

StateMachine::StateMachine()
{
	started = false;
}

void StateMachine::add(Ptr<State> state)
{
	states.push_back(state);
}

void StateMachine::start()
{
	started = true;
	current = states[0];
	current->enter();
}

bool StateMachine::eval()
{
	if (! started) return false;

	for (size_t i = 0; i < current->transitions.count(); ++i) {
		Ptr<Transition> trans = current->transitions[i];
		if (trans->eval()) {
			current->exit();
			current = trans->to_state;
			current->enter();
			return true;
		}
	}

	return false;
}
