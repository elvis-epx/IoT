from epx.loop import Task, SECONDS, MILISSECONDS, Longcronometer
from switch.service import SwitchPub, SwitchSub

class Switch:
    def __init__(self, mqtt, iodriver, pin):
        self.pin = pin
        self.iodriver = iodriver
        self.pin = pin
        name = "%d" % pin
        self.pub = mqtt.pub(SwitchPub(name, self))
        self.sub = mqtt.sub(SwitchSub(name, self))
        # FIXME NVRAM state
        self.state = -1
        self.switch(0)

    def switch(self, new_state):
        new_state = new_state and 1 or 0
        if self.state != new_state:
            self.state = new_state
            self.iodriver.output_pin(self.pin, self.state)
            self.pub.forcepub()
            print("Switch %d = %d" % (self.pin, self.state))
            # FIXME NVRAM support x mode 'mem'

    def is_on(self):
        return self.state
