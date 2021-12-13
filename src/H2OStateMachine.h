#ifndef __H2OSTATES_H
#define __H2OSTATES_H

#include "StateMachine.h"

class Initial: public State {
public:
	virtual void enter();
	virtual void exit();
};

/* Pump off */
class Off: public State {
public:
	virtual void enter();
	virtual void exit();
};

/* Pump off after being on */
class HisteresisOff: public State {
public:
	virtual void enter();
	virtual void exit();
};

/* Pump off due to override-off switch */
class ManualOff: public State {
public:
	virtual void enter();
	virtual void exit();
};

/* Pump on */
class On: public State {
public:
	virtual void enter();
	virtual void exit();
};

/* Pump just turned on */
class HisteresisOn: public State {
public:
	virtual void enter();
	virtual void exit();
};

/* Pump on due to override-on switch */
class ManualOn: public State {
public:
	virtual void enter();
	virtual void exit();
};

/* Water flow not detected, turned pump off.
   Could be: pump w/o water, pump disconnected,
   flow sensor failure, blocked pipe, dry well,
   circuit breaker tripped, etc.
*/
class FlowFailure: public State {
public:
	virtual void enter();
	virtual void exit();
};

/* Level change not detected in spite of water flow
   over enough time, turned pump off.
   Could be: leakage, level sensor failure,
   even false alarm due to high water consumption.
*/
class LevelFailure: public State {
public:
	virtual void enter();
	virtual void exit();
};

class H2OStateMachine: public StateMachine {
public:
	H2OStateMachine();
};

#endif
