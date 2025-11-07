import time
import threading
import sys
import os, os.path
from epx import loop, net, mqtt
import traceback

TEST_ENV = True
test_mocks = {}
pins = []

_wifi = None

def freq(_):
    pass

def unique_id():
    return b'\x11\x22\x33'

class Pin:
    OUT = 1
    IN = 2
    IRQ_RISING = 1
    IRQ_FALLING = 2

    def __init__(self, pin, direction=IN):
        self.pin = pin
        self.direction = direction
        self.counter = 0
        pins.append(self)

    def value(self, n = None):
        if n is not None:
            # write
            if self.direction == Pin.IN:
                return
            open(("pin%d.sim") % self.pin, "w").write(n and "1" or "0")
        else:
            # read
            if self.direction == Pin.OUT:
                return
            try:
                data = open(("pin%d.sim") % self.pin).read()
            except FileNotFoundError:
                return 0
            try:
                return int(data) and 1 or 0
            except ValueError:
                return 0

    def test_mock(self):
        f = "pulse%d.sim" % self.pin
        if os.path.exists(f):
            print("Got pulse%d.sim" % self.pin)
            p = int(open(f).read())
            os.remove(f)
            self.counter += p
            return True
        return False

class Counter:
    def __init__(self, n, pin, **kw):
        self.pin = pin

    def value(self, new_value=None):
        res = self.pin.counter
        if new_value is not None:
            self.pin.counter = new_value
        return res

class UART:
    def __init__(self, n, baudrate):
        pass

class I2C:
    def __init__(self, n, scl, sda):
        pass

class WDT:
    def __init__(self, timeout=5000):
        # always use 2.5 seconds for faster testing
        self.timeout = 2500
        self.reset()
        start_new_thread(self.eval, ())

    def feed(self):
        self.reset()

    def reset(self):
        self.deadline = loop.millis_add(loop.millis(), self.timeout)

    def eval(self):
        while loop.running:
            loop.sleep(1000)
            if loop.millis_diff(self.deadline, loop.millis()) < 0:
                print("*** WDT timeout ***")
                reset()

def start_new_thread(cb, params):
    t = threading.Thread(target=cb, args=params)
    t.start()

def reset():
    print("*** Reboot ***")
    loop.running = False

def test_mock(_):
    f = "quit.sim"
    if os.path.exists(f):
        print("Got quit.sim")
        os.remove(f)
        loop.running = False
        return True

    f = "advance.sim"
    if os.path.exists(f):
        print("Got advance.sim")
        t = int(open(f).read())
        loop.millis_offset += t
        os.remove(f)
        return True

    f = "wdtblock.sim"
    if os.path.exists(f):
        print("Got wdtblock.sim")
        os.remove(f)
        # Cause unexpected blockage on main thread, that should
        # trigger the watchdog protection
        loop.sleep(5000)
        return True
    
    for pin in pins:
        if pin.test_mock():
            return True

    for obj in test_mocks.values():
        if obj and obj.test_mock():
            return True

    return False

DEEPSLEEP = 1

def wake_reason():
    return 0

def print_exception(e, f):
    print(str(e), file=f)

def deepsleep(t):
    f = "quit.sim"
    while True:
        if os.path.exists(f):
            print("Got quit.sim (hibernation)")
            os.remove(f)
            sys.exit(0)
        time.sleep(0.25)

sys.print_exception = print_exception
