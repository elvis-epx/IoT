#ifndef __STATEMACHINE_H
#define __STATEMACHINE_H

#include "Vector.h"
#include "Pointer.h"

typedef bool (*Transition)();

class State {
public:
	State() {};
	virtual ~State() {};

	void add(Transition, const char *, Ptr<State>);

	virtual void enter() = 0;
	virtual void exit() {};
	virtual const char *name() const = 0;

	Vector<Transition> transitions;
	Vector<const char *> tnames;
	Vector<Ptr<State>> to_states;
};

class StateMachine {
public:
	StateMachine();
	void add(Ptr<State>);
	void start();
	bool eval();

	bool started;
	Ptr<State> current;
	Vector<Ptr<State>> states;
};

#endif
