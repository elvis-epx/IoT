#ifndef __STATEMACHINE_H
#define __STATEMACHINE_H

#include "Vector.h"
#include "Pointer.h"
#include "Timer.h"

typedef bool (*Transition)(int);

class State {
public:
    State(int);
    virtual ~State();
    void clear();

    void add(Transition, const char *, Ptr<State>);

    virtual void enter() = 0;
    virtual void exit() {};
    virtual const char *name() const = 0;

protected:
    int id;

private:
    Vector<Transition> transitions;
    Vector<const char *> tnames;
    Vector<Ptr<State>> to_states;

friend class StateMachine;
};

class StateMachine {
public:
    StateMachine(int);
    virtual ~StateMachine();
    void add(Ptr<State>);
    void start();
    bool eval();
    const char *cur_state_name() const;
    Cronometer last_movement() const;

private:
    int id;
    bool started;
    Ptr<State> current;
    Vector<Ptr<State>> states;
    Timeout next_eval;
    Cronometer last_transition;
};

#endif
