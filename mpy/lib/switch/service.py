from epx.mqtt import MQTTPub, MQTTSub
from epx.loop import SECONDS, MINUTES

ON = const(1)
OFF = const(0)

class SwitchPub(MQTTPub):
    def __init__(self, name, switch):
        # client should call forcepub()
        MQTTPub.__init__(self, "stat/%s/" + name + "/State", 1 * MINUTES, 10 * MINUTES, False)
        self.switch = switch

    def gen_msg(self):
        return self.switch.is_on() and "1" or "0"

class SwitchSub(MQTTSub):
    def __init__(self, name, switch):
        self.switch = switch
        MQTTSub.__init__(self, "cmnd/%s/" + name + "/State")

    def recv(self, topic, msg, retained, dup):
        value = msg.lower().strip()
        if value in (b"on", b"1", b"up"):
            self.switch.switch(ON)
        elif value in (b"off", b"0", b"down"):
            self.switch.switch(OFF)
        else:
            print("State: invalid value")

# Manual (pulsing) interruptor

class ManualPub(MQTTPub):
    def __init__(self, source, name, n):
        # client must call forcepub()
        MQTTPub.__init__(self, "stat/%s/Manual" + name + "/Event", 0, 0, False)
        self.source = source
        self.n = n

    def gen_msg(self):
        return self.source.manual_event(self.n)

# Manual interruptor program (map to switches)

class ManualProgPub(MQTTPub):
    def __init__(self, source):
        # client must call forcepub()
        MQTTPub.__init__(self, "stat/%s/Program", 0, 0, False)
        self.source = source

    def gen_msg(self):
        return self.source.program_str()

# Manual program parsing/compilation result

class ManualProgCompilationPub(MQTTPub):
    def __init__(self, source):
        # client must call forcepub()
        MQTTPub.__init__(self, "stat/%s/ProgramCompilation", 0, 0, False)
        self.source = source

    def gen_msg(self):
        return self.source.program_compilation_status()

# Manual program receiver

class ManualProgSub(MQTTSub):
    def __init__(self, source):
        self.source = source
        MQTTSub.__init__(self, "cmnd/%s/Program")

    def recv(self, topic, msg, retained, dup):
        value = msg.decode('utf-8').strip()
        if value:
            self.source.compile_program(value, False)
