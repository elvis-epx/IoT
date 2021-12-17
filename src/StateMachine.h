#ifndef __STATEMACHINE_H
#define __STATEMACHINE_H

#include "Vector.h"
#include "Pointer.h"
#include "Timestamp.h"

typedef bool (*Transition)();

class State {
public:
	State() {};
	virtual ~State();
	void clear();

	void add(Transition, const char *, Ptr<State>);

	virtual void enter() = 0;
	virtual void exit() {};
	virtual const char *name() const = 0;

private:
	Vector<Transition> transitions;
	Vector<const char *> tnames;
	Vector<Ptr<State>> to_states;

friend class StateMachine;
};

class StateMachine {
public:
	StateMachine();
	virtual ~StateMachine();
	void add(Ptr<State>);
	void start();
	bool eval();
	const char *cur_state_name() const;
	Timestamp last_movement() const;

private:
	bool started;
	Ptr<State> current;
	Vector<Ptr<State>> states;
	Timestamp last_transition;
	Timestamp last_eval;
};

#endif
