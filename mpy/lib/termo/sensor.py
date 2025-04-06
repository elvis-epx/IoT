from epx.loop import Task, SECONDS

class Sensor:
    def __init__(self, i2c):
        self._temperature = {}
        self._malfunction = 0

        task = Task(True, "sensor_read", self.eval, 5 * SECONDS)

    def eval(self, _):

    def temperature(self, addr):
        if addr not in self._temperature:
            return None
        return self._temperature[addr]

    def malfunction(self):
        return self._malfunction
