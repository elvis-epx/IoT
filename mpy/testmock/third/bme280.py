import random
import machine
import os
import os.path

BME280_OSAMPLE_4 = 1

singleton = None

def test_mock():
    f = machine.TEST_FOLDER + "bme280.sim"
    if not os.path.exists(f):
        return False
    print("Got bme280.sim")
    data = open(f).read().strip()
    os.remove(f)
    if data == 'fail':
        singleton.fail = True
    else:
        singleton.value = float(data) * 25600.0
    return True

class BME280:
    def __init__(self, i2c, mode):
        global singleton
        singleton = self
        self.value = None
        self.fail = False
        f = machine.TEST_FOLDER + "bme280f.sim"
        if os.path.exists(f):
            print("Got bme280f.sim")
            os.remove(f)
            raise Exception("BME280 simulated failure")

    def read_pressure(self):
        if self.fail:
            raise Exception("BME280 simulated failure")
        if self.value is not None:
            return self.value
        return (1005.0 + random.random() * 10.0) * 256.0 * 100.0
