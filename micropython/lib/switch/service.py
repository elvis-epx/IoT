from epx.mqtt import MQTTPub, MQTTSub
from epx.loop import SECONDS, MINUTES

ON = const(1)
OFF = const(0)

class SwitchPub(MQTTPub):
    def __init__(self, name, switch):
        MQTTPub.__init__(self, "stat/%s/" + name + "/State", 1 * SECONDS, 30 * MINUTES, False)
        self.switch = switch

    def gen_msg(self):
        return self.switch.is_on() and "1" or "0"

class SwitchSub(MQTTSub):
    def __init__(self, name, switch):
        self.switch = switch
        MQTTSub.__init__(self, "cmnd/%s/" + name + "/State")

    def recv(self, topic, msg, retained, dup):
        value = msg.lower().strip()
        if value in ("on", "1", "up"):
            self.switch.switch(ON)
        elif value in ("off", "0", "down"):
            self.switch.switch(OFF)
        else:
            print("State: invalid value msg")


class ManualPub(MQTTPub):
    def __init__(self, source, name, n):
        MQTTPub.__init__(self, "stat/%s/Manual" + name + "/Event", 1 * SECONDS, 24 * 60 * MINUTES, False)
        self.source = source
        self.n = n

    def gen_msg(self):
        return self.source.manual_event(self.n)


class ManualProgPub(MQTTPub):
    def __init__(self, source):
        MQTTPub.__init__(self, "stat/%s/Program", 30 * SECONDS, 24 * 60 * MINUTES, False)
        self.source = source

    def gen_msg(self):
        return self.source.program_str()

class ManualProgSub(MQTTSub):
    def __init__(self, source):
        self.source = source
        MQTTSub.__init__(self, "cmnd/%s/Program")

    def recv(self, topic, msg, retained, dup):
        value = msg.strip()
        if value:
            self.source.compile_program(value)
