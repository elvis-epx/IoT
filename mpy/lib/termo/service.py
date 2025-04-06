from epx.mqtt import MQTTPub
from epx.loop import SECONDS, MINUTES

class Temperatures(MQTTPub):
    def __init__(self, sensor, addr):
        MQTTPub.__init__(self, "stat/%s/Temperature/" + addr, 1 * MINUTES, 10 * MINUTES, False)
        self.addr = addr
        self.sensor = sensor

    def gen_msg(self):
        # as float
        temp = self.sensor.temperature(self.addr)
        if temp is None:
            return None
        return "%.1f" % temp


class Malfunction(MQTTPub):
    def __init__(self, sensor):
        # as integer (bitmap)
        MQTTPub.__init__(self, "stat/%s/Malfunction", 60 * SECONDS, 30 * MINUTES, False)
        self.sensor = sensor

    def gen_msg(self):
        return "%d" % self.sensor.malfunction()
