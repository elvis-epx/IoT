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
        if failsim == "init":
            raise HX711Exception()
        pass

    def read(self):
        return 50.0

    def power_off(self):
        pass
