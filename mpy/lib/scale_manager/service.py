from epx.mqtt import MQTTPub, MQTTSub
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
        MQTTPub.__init__(self, "stat/%s/Malfunction", 0, 0, False)
        self.sensor = sensor

    def gen_msg(self):
        w = self.sensor.malfunction()
        return (w is not None) and ("%d" % w) or None

class PairSub(MQTTSub):
    def __init__(self, netnow):
        MQTTSub.__init__(self, "cmnd/%s/OpenToPair")
        self.netnow = netnow

    def recv(self, topic, msg, retained, dup):
        if len(msg) > 0:
            self.netnow.opentopair()
