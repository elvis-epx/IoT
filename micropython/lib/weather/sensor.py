from third.hdc1080 import HDC1080
from third.bme280 import BME280, BME280_OSAMPLE_4
from epx.loop import Task, SECONDS

class Sensor:
    def __init__(self, i2c):
        self._temperature = None
        self._humidity = None
        self._pressure = None
        self._malfunction = 0

        try:
            self.hdc1080 = HDC1080(i2c)
            print("HDC1080 device up")
        except:
            print("HDC1080 device not working")
            self.hdc1080 = None
            self._malfunction |= 1

        try:
            self.bme280 = BME280(i2c=i2c, mode=BME280_OSAMPLE_4)
            print("BME280 device up")
        except:
            print("BME280 device not working")
            self.bme280 = None
            self._malfunction |= 2

        # Give time for tne sensors to init
        task = Task(False, "sensor", self.enable, 15 * SECONDS)

    def enable(self, _):
        task = Task(True, "sensor_read", self.eval, 60 * SECONDS)
        task.advance()

    def eval(self, _):
        if self.hdc1080:
            try:
                self._humidity = self.hdc1080.read_humidity() + 0.0
                self._malfunction &= ~4
            except:
                print("Cannot read humidity")
                self._malfunction |= 4

            try:
                self._temperature = self.hdc1080.read_temperature(celsius=True) + 0.0
                self._malfunction &= ~8
            except:
                print("Cannot read temperature")
                self._malfunction |= 8

        if self.bme280:
            try:
                self._pressure = self.bme280.read_pressure() / 25600.0
                self._malfunction &= ~16
            except:
                print("Cannot read pressure")
                self._malfunction |= 16
                self._pressure = None

    def temperature(self):
        return self._temperature

    def humidity(self):
        return self._humidity

    def pressure(self):
        return self._pressure

    def malfunction(self):
        return self._malfunction
