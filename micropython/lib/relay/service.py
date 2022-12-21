from epx.mqtt import MQTTPub, MQTTSub
from epx.loop import SECONDS, MINUTES

MAX_TIMEOUT = 600 # civil seconds

class RelayPub(MQTTPub):
    def __init__(self, number, actuator):
        sn = "%s" % number
        MQTTPub.__init__(self, "stat/%s/" + sn + "/State", 1 * SECONDS, 30 * MINUTES, False)
        self.actuator = actuator

    def gen_msg(self):
        return self.actuator.is_on() and "1" or "0"


class RelaySub(MQTTSub):
    def __init__(self, number, actuator):
        sn = "%s" % number
        self.actuator = actuator
        MQTTSub.__init__(self, "cmnd/%s/" + sn + "/TurnOnWithTimeout")

    def recv(self, topic, msg, retained, dup):
        try:
            timeout = int(msg)
        except ValueError:
            print("TurnOnWithTimeout: invalid value msg")
            return

        if timeout < 0:
            timeout = 0
        elif timeout > MAX_TIMEOUT:
            timeout = MAX_TIMEOUT
        self.actuator.turn_on_with(timeout)
