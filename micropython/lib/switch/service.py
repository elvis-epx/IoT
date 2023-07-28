from epx.mqtt import MQTTPub, MQTTSub
from epx.loop import SECONDS, MINUTES

ON = const(1)
OFF = const(0)

class SwitchPub(MQTTPub):
    def __init__(self, name, actuator):
        MQTTPub.__init__(self, "stat/%s/" + name + "/State", 1 * SECONDS, 30 * MINUTES, False)
        self.actuator = actuator

    def gen_msg(self):
        return self.actuator.is_on() and "1" or "0"

class SwitchSub(MQTTSub):
    def __init__(self, name, actuator):
        self.actuator = actuator
        MQTTSub.__init__(self, "cmnd/%s/" + name + "/State")

    def recv(self, topic, msg, retained, dup):
        value = value.lower().strip()
        if value in ("on", "1", "up"):
            self.actuator.switch(ON)
        elif value in ("off", "0", "down"):
            self.actuator.switch(OFF)
        else:
            print("State: invalid value msg")
