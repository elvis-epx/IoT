import random
import machine
import os
import os.path

singleton = None

def test_mock():
    f = machine.TEST_FOLDER + "pzem.sim"
    if not os.path.exists(f):
        return False
    print("Got pzem.sim")
    data = open(f).read().strip()
    os.remove(f)
    if data == 'fail1':
        singleton.fail = 1
    elif data == 'fail2':
        singleton.fail = 2
    elif data == 'fail4':
        singleton.fail = 4
    else:
        singleton.fail = 0
    return True

class PZEM:
    def __init__(self, uart, addr=0xF8):
        global singleton
        singleton = self
        self.fail = 0
        self.res = True
        pass

    def check_addr_start(self):
        self.read_addr_start()

    def read_addr_start(self):
        self.res = self.fail != 1

    def read_energy_start(self):
        self.res = self.fail != 4

    def reset_energy_start(self):
        self.res = self.fail != 2

    def complete_trans(self):
        return self.res

    def get_data(self):
        return {"V": 222.1,
                "A": 4.8,
                "W": 0.0,
                "Wh": 150,
                "Hz": 60.0,
                "pf": 0.7}
