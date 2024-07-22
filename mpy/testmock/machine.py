import time
import threading
import sys
import os, os.path
from epx import loop, net, mqtt
import traceback

TEST_ENV = True
TEST_FOLDER = "."
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
        self.irq_cb = None
        pins.append(self)

    def value(self, n = None):
        if n is not None:
            # write
            if self.direction == Pin.IN:
                return
            open((TEST_FOLDER + "/" + "pin%d.sim") % self.pin, "w").write(n and "1" or "0")
        else:
            # read
            if self.direction == Pin.OUT:
                return
            try:
                data = open((TEST_FOLDER + "/" + "pin%d.sim") % self.pin).read()
            except FileNotFoundError:
                return 0
            try:
                return int(data) and 1 or 0
            except ValueError:
                return 0

    def irq(self, trigger, handler):
        self.irq_cb = handler

    def test_mock(self):
        f = TEST_FOLDER + ("pulse%d.sim" % self.pin)
        if os.path.exists(f):
            print("Got pulse%d.sim" % self.pin)
            p = int(open(f).read())
            os.remove(f)
            for _ in range(0, p):
                self.irq_cb(None)
            return True
        return False

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
    f = TEST_FOLDER + "quit.sim"
    if os.path.exists(f):
        print("Got quit.sim")
        os.remove(f)
        loop.running = False
        return True

    f = TEST_FOLDER + "advance.sim"
    if os.path.exists(f):
        print("Got advance.sim")
        t = int(open(f).read())
        loop.millis_offset += t
        os.remove(f)
        return True

    f = TEST_FOLDER + "wdtblock.sim"
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

sys.print_exception = print_exception
