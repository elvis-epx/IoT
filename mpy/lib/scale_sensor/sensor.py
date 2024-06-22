from epx.loop import Task, SECONDS
from epx.third.hx711 import HX711, HX711Exception

class Sensor:
    def __init__(self, cfg, watchdog):
        self.a = float(cfg.data['calibration_a'])
        self.b = float(cfg.data['calibration_b'])
        self.max_samples = 12
        self.min_samples = 8
        self.max_deviation = 200
        self.max_retries = 3

        self._weight = None
        self._malfunction = None
        task = Task(False, "sensor", self.enable, (watchdog.grace_time() + 1) * SECONDS)
        self.impl = None

    def enable(self, _):
        print("Sensor.enable")

        self._weight = None
        self._malfunction = None

        if not self.impl:
            try:
                self.impl = HX711(d_out=5, pd_sck=4)
            except HX711Exception:
                self._malfunction = 1
                return
        else:
            try:
                self.impl.power_on()
            except HX711Exception:
                self._malfunction = 2
                return

        self.reset_sampling()
        # warmup
        task = Task(True, "sensor_sample", self.take_sample, 10 * SECONDS)

    def reset_sampling(self):
        self.samples = []
        self.retries = 0

    def take_sample(self, _):
        print("Sensor.take_sample")
        try:
            reading = self.impl.read()
        except HX711Exception:
            self._malfunction = 4
            return

        if not self.eval_sample(reading):
            self._malfunction = 8
            return

        task = Task(True, "sensor_sample", self.take_sample, 1 * SECONDS)

    def eval_sample(self, reading):
        self.samples.append(reading)

        # Take a number of samples then calculate the mean to find weight
        if len(self.samples) < self.max_samples:
            return True

        # Provisional mean to filter out aberrant samples 
        mean = sum(self.samples) / len(self.samples)
        self.samples = list(filter(lambda w: abs(w - mean) < self.max_deviation, self.samples))

        if len(self.samples) < self.min_samples:
            # Too many aberrant readings
            self.reset_sampling()
            self.retries += 1
            if self.retries > self.max_retries:
                # Quit
                return False
            # Retry
            return True

        # Final mean and interpolation
        mean = sum(self.samples) / len(self.samples)
        self._weight = mean * self.a + self.b

        # Start over
        self.reset_sampling()
        return True

    def weight(self):
        return self._weight, self._malfunction

    def disable(self):
        print("Sensor.disable")
        self.impl.power_off()
