#include "StateMachine.h"
#include <stdio.h>

void State::add(Transition trans, const char *tname, Ptr<State> to_state)
{
	transitions.push_back(trans);
	tnames.push_back(tname);
	to_states.push_back(to_state);
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
		Transition trans = current->transitions[i];
		if (trans()) {
			auto next = current->to_states[i];
			printf("trans %s, st %s -> %s\n", current->tnames[i], current->name(), next->name());
			current->exit();
			current = next;
			current->enter();
			return true;
		}
	}

	return false;
}
