from epx.mqtt import MQTTPub
from epx.loop import SECONDS, MINUTES

class WeightPub(MQTTPub):
    def __init__(self, sensor):
        # client must call forcepub() manually
        MQTTPub.__init__(self, "stat/%s/Weight", 0, 0, False)
        self.sensor = sensor

    def gen_msg(self):
        w = self.sensor.weight()
        return (w is not None) and ("%.3f" % w) or None

class MalfunctionPub(MQTTPub):
    def __init__(self, sensor):
        # client must call forcepub() manually
        MQTTPub.__init__(self, "stat/%s/Weight", 0, 0, False)
        self.sensor = sensor

    def gen_msg(self):
        w = self.sensor.malfunction()
        return (w is not None) and ("%d" % w) or None
