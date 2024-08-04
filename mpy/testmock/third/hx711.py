import random
import machine
import os
import os.path

failsim = 0

def test_mock():
    global failsim
    f = machine.TEST_FOLDER + "hx711.sim"
    if not os.path.exists(f):
        return False
    print("Got hx711.sim")
    data = open(f).read().strip()
    os.remove(f)
    if data == 'fail1':
        failsim = 1
    elif data == 'fail2':
        failsim = 2
    elif data == 'fail4':
        failsim = 4
    else:
        failsim = 0
    return True

class HX711Exception(Exception):
    pass

class HX711:
    def __init__(self, d_out, pd_sck):
        global singleton
        singleton = self
        pass

    def read(self):
        return 50.0

    def power_off(self):
        pass
