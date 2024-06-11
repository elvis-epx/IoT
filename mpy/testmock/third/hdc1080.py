import random
import os
import os.path
import machine

singleton = None

def test_mock():
    f = machine.TEST_FOLDER + "hdc1080.sim"
    if not os.path.exists(f):
        return False
    print("Got hdc1080.sim")
    data = open(f).read().strip()
    os.remove(f)
    if data == 'fail':
        singleton.fail = True
    else:
        singleton.temp, singleton.hum = [ float(n.strip()) for n in data.split(',')]
    return True

class HDC1080:
    def __init__(self, i2c):
        global singleton
        singleton = self
        self.temp = None
        self.hum = None
        self.fail = False
        f = machine.TEST_FOLDER + "hdc1080f.sim"
        if os.path.exists(f):
            print("Got hdc1080f.sim")
            os.remove(f)
            raise Exception("HDC1080 simulated failure")

    def read_temperature(self, celsius=False):
        if self.fail:
            raise Exception("HDC1080 simulated failure")
        if self.temp is not None:
            temp = self.temp
        else:
            temp = 20.0 + random.random() * 7.0
        if celsius:
            return temp
        else:
            return temp * 9.0 / 5.0 + 32.0

    def read_humidity(self):
        if self.fail:
            raise Exception("HDC1080 simulated failure")
        if self.hum is not None:
            return self.hum
        return 80.0 + random.random() * 5.0
