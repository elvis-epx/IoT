import random
import machine
import os
import os.path

failsim = ""

def test_mock():
    global failsim
    f = "hx711f.sim"
    if not os.path.exists(f):
        return False
    print("Got hx711f.sim")
    data = open(f).read().strip()
    os.remove(f)
    failsim = data
    return True

class HX711Exception(Exception):
    pass

class HX711:
    def __init__(self, d_out, pd_sck):
        global singleton
        singleton = self
        self.reads = 0
        if failsim == "init":
            raise HX711Exception()
        pass

    def read(self):
        if failsim == "read":
            raise HX711Exception()
        self.reads += 1
        if failsim == "unstable" and self.reads < 12:
            # 12 comes from lib/scale_sensor/sensor.py:max_samples
            return 50.0 - self.reads
        elif failsim == "unstable2":
            return 50.0 + self.reads
        return 50.0

    def power_off(self):
        if failsim == "poweroff":
            raise HX711Exception()
        pass
