#ifndef __STATEMACHINE_H
#define __STATEMACHINE_H

#include "Vector.h"
#include "Pointer.h"

class State;

class Transition {
public:
	Transition(Ptr<State> to_state): to_state(to_state) {};
	virtual ~Transition() {};
	virtual bool eval() { return false; };
	virtual const char *name() { return "Invalid Transition"; };

	Ptr<State> to_state;
};

class State {
public:
	State() {};
	virtual ~State() {};

	void add(Ptr<Transition>);

	virtual void enter() {};
	virtual void exit() {};
	virtual const char *name() const { return "Invalid State"; };

	Vector<Ptr<Transition>> transitions;
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
