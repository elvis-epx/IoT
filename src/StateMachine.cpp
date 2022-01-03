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

State::~State()
{
}

void State::clear()
{
	// explicit break of cyclic references to please Valgrind
	to_states.clear();
}

StateMachine::StateMachine()
{
	started = false;
	last_transition = now();
	last_eval = now();
}

StateMachine::~StateMachine()
{
	// Break State->Transition->State cycle to please Valgrind
	for (size_t i = 0; i < states.count(); ++i) {
		states[i]->clear();
	}
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

Timestamp StateMachine::last_movement() const
{
	return last_transition;
}
