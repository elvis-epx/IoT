import gc
import time
import random
import machine

MILISSECONDS = const(1)
SECONDS = const(1000 * MILISSECONDS)
MINUTES = (60 * SECONDS)

running = True
millis_offset = 0 # used to fast-forward time in tests

class Cronometer:
    def __init__(self):
        self.restart()

    def restart(self):
        self.base = millis()

    def elapsed(self):
        return millis_diff(millis(), self.base)


class StateMachine:
    def __init__(self, name):
        self.name = name
        self.states = {"initial": None}
        self.transitions = {}
        self.tasks = []
        self.state = "initial"
        self.observers = {}

    def add_state(self, name, callback):
        self.states[name] = callback

    def add_transition(self, from_name, to_name):
        if from_name not in self.transitions:
            self.transitions[from_name] = {}
        self.transitions[from_name][to_name] = 1

    def attach(self, task):
        self.tasks.append(task)

    def recurring_task(self, name, cb, to, fudge=0):
        tsk = Task(True, name, cb, to, fudge)
        self.attach(tsk)
        return tsk

    def onetime_task(self, name, cb, to, fudge=0):
        tsk = Task(False, name, cb, to, fudge)
        self.attach(tsk)
        return tsk

    def cancel_state_tasks(self):
        for task in self.tasks:
            task.cancel()
        self.tasks = []

    def schedule_trans(self, new_state, to, fudge=0):
        name = self.name + "$" + self.state + "$" + new_state
        def cb(_):
            self._trans(new_state)
        self.onetime_task(name, cb, to, fudge)

    def schedule_trans_now(self, new_state):
        self.cancel_state_tasks()
        self.schedule_trans(new_state, 0)

    def run_observers(self):
        for name in list(self.observers.keys()):
            if name in self.observers:
                state, cb = self.observers[name]
                if state == self.state:
                    del self.observers[name]
                    cb()

    def observe(self, name, state, cb):
        self.observers[name] = (state, cb)
        self.run_observers()

    def _trans(self, to_state):
        if to_state not in self.transitions[self.state]: # pragma: no cover
            print("*** Invalid trans %s %s %s" % (self.name, self.state, to_state))
            return False
        self.cancel_state_tasks()
        print("%s: %s -> %s" % (self.name, self.state, to_state))
        self.state = to_state
        self.states[self.state]()
        self.run_observers()


tasks = {}

class Task:
    last_id = 0

    def __init__(self, recurring, name, cb, delay, fudge=0):
        global last_id
        self.recurring = recurring
        self.name = name
        self.cb = cb
        self.delay = delay
        self.fudge = fudge
        Task.last_id += 1
        self.nid = Task.last_id
        self.restart()
        # print("Scheduled task %s %d" % (self.name, self.nid))

    def restart(self):
        tasks[self.nid] = self
        delta = self.delay
        if self.fudge:
            rnd = random.getrandbits(8)
            delta += (self.fudge * rnd) // 256
        self.time_due = millis_add(millis(), delta)

    def advance(self):
        self.time_due = millis()

    def due(self):
        return self.time_due

    def run(self):
        # print("Running task %s %d" % (self.name, self.nid))
        self._remove()
        self.cb(self)
        # Note that callback may cancel() a recurring task or restart a one-time task
        if self.recurring:
            self.restart()
            # print("Restarted task %s %d" % (self.name, self.nid))

    def cancel(self):
        self.recurring = False
        self._remove()
        # print("Cancelled task %s %d" % (self.name, self.nid))

    def _remove(self):
        if self.nid in tasks:
            del tasks[self.nid]

def next_task():
    now = millis()
    chosen_task = None
    chosen_due = None
    for task in tasks.values():
        due = task.due()
        if (chosen_due is None) or millis_diff(due, chosen_due) < 0:
            chosen_task, chosen_due = task, due
    return chosen_task, millis_diff(chosen_due, millis())

def do_gc(_):
    gc.collect()
    print("Mem alloc", gc.mem_alloc(), "free", gc.mem_free())

def sleep(ms):
    if ms < 0:
        ms = 0
    time.sleep_ms(ms)

def millis():
    return millis_add(time.ticks_ms(), millis_offset)

def millis_diff(a, b):
    return time.ticks_diff(a, b)

def millis_add(a, b):
    return time.ticks_add(a, b)

def run():
    gc_task = Task(True, "gc", do_gc, 1 * MINUTES)
    led = machine.Pin(2, machine.Pin.OUT)

    if hasattr(machine, 'TEST_ENV'):
        test_task = Task(True, "testh", machine.test_mock, 1 * SECONDS)

    while running:
        task, t = next_task()
        sleep(t)
        led.value(1)
        task.run()
        led.value(0)

def reboot():
    machine.reset()
