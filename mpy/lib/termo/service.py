from epx.mqtt import MQTTPub
from epx.loop import SECONDS, MINUTES

class Temperatures(MQTTPub):
    def __init__(self, sensor, addr):
        MQTTPub.__init__(self, "stat/%s/Temperature/" + addr, 15 * SECONDS, 5 * MINUTES, False)
        self.addr = addr
        self.sensor = sensor
        self.last_temp = None

    def gen_msg(self):
        # as float
        temp, accuracy_stddev = self.sensor.temperature(self.addr)
        if temp is None:
            return None
        # TODO move precision (0.1 in this case) to config.txt
        if self.last_temp is not None and abs(temp - self.last_temp) < max(0.1, accuracy_stddev):
            # Avoid dithering
            temp = self.last_temp
        else:
            self.last_temp = temp
        return "%.1f" % temp


class Malfunction(MQTTPub):
    def __init__(self, sensor):
        # as integer (bitmap)
        MQTTPub.__init__(self, "stat/%s/Malfunction", 60 * SECONDS, 30 * MINUTES, False)
        self.sensor = sensor

    def gen_msg(self):
        v = self.sensor.malfunction()
        if v is None:
            return None
        return "%d" % v
