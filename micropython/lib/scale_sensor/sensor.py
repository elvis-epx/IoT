from epx.loop import Task, SECONDS

class Sensor:
    def __init__(self, cfg):
        self.a = float(self.cfg['calibration_a'])
        self.b = float(self.cfg['calibration_b'])
        self._weight = None
        self._malfunction = None

        # Give time for the sensors (and watchdog) to init
        task = Task(False, "sensor", self.enable, 15 * SECONDS)

    def enable(self, _):
        # FIXME enable sensor pin
        # FIXME consider warm-up time?       
        task = Task(True, "sensor_read", self.eval, 10 * SECONDS)

    def eval(self, _):
        # FIXME talk with sensor
        import random
        self._weight = 23.45 + random.random()

    def weight(self):
        return self._weight, self._malfunction

    def disable(self):
        # FIXME implement?
        pass
