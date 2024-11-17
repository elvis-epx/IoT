import gc
import time
import random
import machine
import sys
import select

MILISSECONDS = const(1)
SECONDS = const(1000 * MILISSECONDS)
MINUTES = (60 * SECONDS)

running = True
millis_offset = 0 # used to fast-forward time in tests

class Shortcronometer:
    def __init__(self):
        self.restart()

    def restart(self):
        self.base = millis()

    def elapsed(self):
        return millis_diff(millis(), self.base)


class Longcronometer:
    def __init__(self):
        self.restart()

    def restart(self):
        self.base = time.time() # integer in MicroPython

    def elapsed(self):
        return (time.time() - self.base) * 1000


class StateMachine:
    def __init__(self, name):
        self.name = name
        self.states = {"initial": None}
        self.transitions = {}
        self.tasks = []
        self.polls = []
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

    def deattach(self, task):
        self.tasks.remove(task)

    # FIXME not detached if cancelled by client
    def recurring_task(self, name, cb, to, fudge=0):
        tsk = Task(True, name, cb, to, fudge)
        self.attach(tsk)
        return tsk

    # FIXME not detached if cancelled by client
    def onetime_task(self, name, cb, to, fudge=0):
        def cb_in(task):
            self.deattach(task)
            cb(task)
        tsk = Task(False, name, cb_in, to, fudge)
        self.attach(tsk)
        return tsk

    def poll_object(self, name, obj, mask, cb):
        poll_name = self.name + "_" + name
        poll_object(poll_name, obj, mask, cb)
        self.polls.append(poll_name)

    def cancel_state_tasks(self):
        for task in self.tasks:
            task.cancel()
        self.tasks = []
        for poll_name in self.polls:
            unpoll_object(poll_name)
        self.polls = []

    def schedule_trans(self, new_state, to, fudge=0):
        name = self.name + "$" + self.state + "$" + new_state
        def cb(_):
            self._trans(new_state)
        tsk = Task(False, name, cb, to, fudge)
        self.attach(tsk)

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
        if delay >= 0x40000000: # pragma: no cover
            # time.ticks_ms() wraps in 31 or 32 bits, so tasks can't be longer than 12 days or so
            raise Exception("Task too long TODO add support to long timeouts")
        self.fudge = fudge
        Task.last_id += 1
        self.nid = Task.last_id
        self.restart()
        # print("Scheduled task %s %d" % (self.name, self.nid))

    def restart(self):
        tasks[self.nid] = self
        delta = self.delay
        if self.fudge:
            rnd = random.getrandbits(24) / 2 ** 24
            delta += int(self.fudge * rnd)
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
    time.sleep_ms(max(ms, 0))

def millis():
    return millis_add(time.ticks_ms(), millis_offset)

def millis_diff(a, b):
    return time.ticks_diff(a, b)

def millis_add(a, b):
    return time.ticks_add(a, b)

polls = {}
opoll = select.poll()
POLLIN = select.POLLIN
POLLOUT = select.POLLOUT
POLLHUP = select.POLLHUP
POLLERR = select.POLLERR
POLLNVAL = 32 # when WiFi is inactive or disconnected

def poll_object(name, obj, mask, cb):
    if hasattr(machine, 'TEST_ENV'):
        # in regular Python, poll.poll() returns file descriptors, not objects
        obj = obj.fileno()
    unpoll_object(name)
    polls[name] = {"obj": obj, "mask": mask, "cb": cb}
    opoll.register(obj, mask)

def unpoll_object(name):
    if name in polls:
        opoll.unregister(polls[name]["obj"])
        del polls[name]

def handle_poll_res(res):
    for ptuple in res:
        obj, flags = ptuple[0], ptuple[1]
        for name in list(polls.keys()):
            d = polls[name]
            if d["obj"] is obj:
                if flags & (POLLHUP | POLLERR | POLLNVAL):
                    unpoll_object(name)
                    # Last call for the callback to handle the error
                d["cb"](flags)
                break

def get_any_poll_obj(): # pragma: no cover
    return polls[list(polls.keys())[0]]

def run(led_pin=2, led_inverse=0):
    try:
        gc_task = Task(True, "gc", do_gc, 1 * MINUTES)

        led = (led_pin > 0) and machine.Pin(led_pin, machine.Pin.OUT) or None
    
        if hasattr(machine, 'TEST_ENV'):
            test_task = Task(True, "testh", machine.test_mock, 250 * MILISSECONDS)
    
        while running:
            task, t = next_task()

            if t > 0:
                try:
                    poll_res = opoll.poll(t)
                except OSError: # pragma: no cover
                    # "Should not happen", seems to be a MicroPython-only behavior
                    # when the underlying network interface fails
                    # (extmod/modusocket.c, function socket_ioctl)
                    #
                    # Difficult to simulate in coverage test - CPython3 does not raise
                    # at poll.poll() for any error, so coverage disabled
                    #
                    # Cannot pinpoint the offending file descriptor, so we report anyone
                    # as POLLERR (which excludes it from polling). In the worst case,
                    # it will keep excluding sockets until the culprit is reached.
                    poll_res = ((get_any_poll_obj(), POLLERR),)
            else:
                poll_res = None

            if led:
                led.value(not led_inverse)

            if poll_res:
                handle_poll_res(poll_res)
            else:
                task.run()

            if led:
                led.value(led_inverse)

    except Exception as e:
        with open("exception.txt", "w") as f:
            sys.print_exception(e, f)
        raise

def reboot(reason=""):
    print(reason)
    with open("reboot.txt", "w") as f:
        print(reason, file=f)
    machine.reset()

def hibernate(t):
    machine.deepsleep(t)
