from epx.loop import Task, SECONDS
from third.hx711 import HX711, HX711Exception

class Sensor:
    def __init__(self, cfg, watchdog):
        self.a = float(cfg.data['calibration_a'])
        self.b = float(cfg.data['calibration_b'])
        self.max_samples = 12
        self.min_samples = 8
        self.max_deviation = 0.050 # kg
        self.max_retries = 3

        self._weight = None
        self._malfunction = None
        task = Task(False, "sensor", self.enable, (watchdog.grace_time() + 1) * SECONDS)
        self.impl = None
        self.sampling_task = None

    def enable(self, _):
        print("Sensor.enable")

        self._weight = None
        self._malfunction = None

        try:
            self.impl = HX711(d_out=5, pd_sck=4)
        except HX711Exception:
            print("Could not connect with hx711")
            self._malfunction = 1
            return False

        self.samples = []
        self.retries = 0
        # warmup
        self.sampling_task = Task(False, "sensor_sample", self.take_sample, 10 * SECONDS)
        return True

    def take_sample(self, _):
        print("Sensor.take_sample")
        self.sampling_task = None

        try:
            reading = self.impl.read()
        except HX711Exception:
            print("Could not read from hx711")
            self._malfunction = 4
            return

        if not self.eval_sample(reading):
            self._malfunction = 8
            return

        self.sampling_task = Task(False, "sensor_sample", self.take_sample, 1 * SECONDS)

    def eval_sample(self, reading):
        weight = (reading + self.b) / self.a
        self.samples.append(weight)
        print(reading, weight)

        # Take a number of samples then calculate the mean to find weight
        if len(self.samples) < self.max_samples:
            print("Need more samples")
            return True

        # Provisional mean to filter out aberrant samples 
        mean = sum(self.samples) / len(self.samples)
        self.samples = list(filter(lambda w: abs(w - mean) < self.max_deviation, self.samples))

        if len(self.samples) < self.min_samples:
            # Too many aberrant readings
            self.samples = []
            self.retries += 1
            if self.retries > self.max_retries:
                print("Too many retries, quit")
                return False
            print("Too much deviation, retry")
            return True

        self._weight = sum(self.samples) / len(self.samples)
        print("Mean weight", self._weight)

        # Start over
        self.samples = []
        self.retries = 0
        return True

    def weight(self):
        return self._weight, self._malfunction

    def disable(self):
        print("Sensor.disable")
        if self.sampling_task:
            self.sampling_task.cancel()
            self.sampling_task = None
        if self.impl:
            try:
                self.impl.power_off()
            except HX711Exception:
                print("Could not power hx711 off")
                pass
        self.impl = None

