import random
import machine
import os
import os.path

failsim = 0

def test_mock():
    global failsim
    f = "pzem.sim"
    if not os.path.exists(f):
        return False
    print("Got pzem.sim")
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

class PZEM:
    def __init__(self, uart, addr=0xF8):
        global singleton
        singleton = self
        self.res = True
        pass

    def check_addr_start(self):
        self.read_addr_start()

    def read_addr_start(self):
        global failsim
        self.res = failsim != 1

    def read_energy_start(self):
        global failsim
        self.res = failsim != 4

    def reset_energy_start(self):
        global failsim
        self.res = failsim != 2

    def complete_trans(self):
        return self.res

    def get_data(self):
        return {"V": 222.1,
                "A": 4.8,
                "W": 0.0,
                "Wh": 150,
                "Hz": 60.0,
                "pf": 0.7}
