#ifndef __H2OSTATES_H
#define __H2OSTATES_H

#include "StateMachine.h"

class Initial: public State {
public:
	virtual void enter();
	virtual const char* name() const { return "Initial"; };
};

/* Pump off */
class Off: public State {
public:
	virtual void enter();
	virtual const char* name() const { return "Off"; };
};

/* Pump off after being on */
class HisteresisOff: public State {
public:
	virtual void enter();
	virtual const char* name() const { return "Off - rest"; };
};

/* Pump off due to override-off switch */
class ManualOff: public State {
public:
	virtual void enter();
	virtual const char* name() const { return "Off (manual)"; };
};

/* Pump on */
class On: public State {
public:
	virtual void enter();
	virtual const char* name() const { return "On"; };
};

/* Pump on due to override-on switch */
class ManualOn: public State {
public:
	virtual void enter();
	virtual const char* name() const { return "On (manual)"; };
};

/* Water flow not detected, turned pump off.
   Could be: pump w/o water, pump disconnected,
   flow sensor failure, blocked pipe, dry well,
   circuit breaker tripped, etc.
*/
class FlowFailure: public State {
public:
	virtual void enter();
	virtual const char* name() const { return "Flow failure"; };
};

/* Level change not detected in spite of water flow
   over enough time, turned pump off.
   Could be: leakage, level sensor failure,
   even false alarm due to high water consumption.
*/
class LevelFailure: public State {
public:
	virtual void enter();
	virtual const char* name() const { return "Level failure"; };
};

class H2OStateMachine: public StateMachine {
public:
	H2OStateMachine();
};

#endif
