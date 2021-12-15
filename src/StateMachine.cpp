#include "StateMachine.h"
#include <stdio.h>
#include "Display.h"

extern Display display;

void State::add(Transition trans, const char *tname, Ptr<State> to_state)
{
	transitions.push_back(trans);
	tnames.push_back(tname);
	to_states.push_back(to_state);
}

StateMachine::StateMachine()
{
	started = false;
	last_transition = 0;
	last_eval = 0;
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

	if ((now() - last_eval) < 500) {
		return false;
	}

	last_eval = now();

	for (size_t i = 0; i < current->transitions.count(); ++i) {
		Transition trans = current->transitions[i];
		if (trans()) {
			auto next = current->to_states[i];
			char msg[80];
			sprintf(msg, "trans %s, st %s -> %s", current->tnames[i],
					current->name(), next->name());
			display.debug(msg);
			current->exit();
			current = next;
			current->enter();
			last_transition = now();
			return true;
		}
	}

	return false;
}

const char* StateMachine::cur_state_name() const
{
	return current->name();
}

Timestamp StateMachine::since_last_transition() const
{
	return now() - last_transition;
}
