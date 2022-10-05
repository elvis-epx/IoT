#ifndef __H2OSTATES_H
#define __H2OSTATES_H

#include "StateMachine.h"

class Initial: public State {
public:
    Initial(int);
    virtual void enter();
    virtual const char* name() const { return "Initial"; };
};

/* Pump off */
class Off: public State {
public:
    Off(int);
    virtual void enter();
    virtual const char* name() const { return "Off"; };
};

/* Pump off after being on */
class HisteresisOff: public State {
public:
    HisteresisOff(int);
    virtual void enter();
    virtual const char* name() const { return "Resting"; };
};

/* Pump off due to override-off MQTT switch */
class ManualOff: public State {
public:
    ManualOff(int);
    virtual void enter();
    virtual const char* name() const { return "Off MQTT"; };
};

/* Pump on */
class On: public State {
public:
    On(int);
    virtual void enter();
    virtual const char* name() const { return "On"; };
};

/* Pump on due to override-on MQTT switch */
class ManualOn: public State {
public:
    ManualOn(int);
    virtual void enter();
    virtual const char* name() const { return "On MQTT"; };
};

/* Water flow not detected, turned pump off.
   Could be: pump w/o water, pump disconnected,
   flow sensor failure, blocked pipe, dry well,
   circuit breaker tripped, etc.
*/
class FlowFailure: public State {
public:
    FlowFailure(int);
    virtual void enter();
    virtual const char* name() const { return "F flow"; };
};

/* Water flow detected but unexpectedly low, over last 1-2 minutes,
   turned pump off.
   Could be: drying well, flow sensor failure, blocked pipe.
*/
class LowFlowShort: public State {
public:
    LowFlowShort(int);
    virtual void enter();
    virtual const char* name() const { return "F slow 2"; };
};

/* Water flow detected but unexpectedly low, over last 30 minutes,
   turned pump off.
   Could be: drying well, flow sensor failure, blocked pipe.
*/
class LowFlowLong: public State {
public:
    LowFlowLong(int);
    virtual void enter();
    virtual const char* name() const { return "F slow 30"; };
};

/* Pump running too much time
   Could be: low flow (but not too low to trigger LowFlow),
   comsumption of water bigger than pumping capacity, 
   constants at Constants.h too wrong
*/
class PumpTimeout: public State {
public:
    PumpTimeout(int);
    virtual void enter();
    virtual const char* name() const { return "F timeout"; };
};

/* Level change not detected in spite of water flow
   over enough time, turned pump off.
   Could be: leakage, level sensor failure,
   even false alarm due to high water consumption.
*/
class LevelFailure: public State {
public:
    LevelFailure(int);
    virtual void enter();
    virtual const char* name() const { return "F level"; };
};

class H2OStateMachine: public StateMachine {
public:
    H2OStateMachine();
private:
    
};

#endif
