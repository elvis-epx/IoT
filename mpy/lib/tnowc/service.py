from epx.mqtt import MQTTPub
from epx.loop import SECONDS, MINUTES

class TNowPub(MQTTPub):
    def __init__(self, sensor):
        # client must call forcepub() manually
        MQTTPub.__init__(self, "stat/%s/Value", 0, 0, False)
        self.sensor = sensor

    def gen_msg(self):
        return self.sensor.value()
