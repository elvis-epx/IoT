from epx.loop import Task, SECONDS, MILISSECONDS, Longcronometer
from switch.service import SwitchPub, SwitchSub

class Switch:
    def __init__(self, nvram, mqtt, iodriver, pin):
        self.nvram = nvram
        self.pin = pin
        self.iodriver = iodriver
        self.pin = pin
        self.name = "%d" % pin
        self.pub = mqtt.pub(SwitchPub(self.name, self))
        self.sub = mqtt.sub(SwitchSub(self.name, self))
        self.state = -1

        stored = self.nvram.get_int(self.name) and 1 or 0
        self.switch(stored)

    def switch(self, new_state):
        new_state = new_state and 1 or 0
        if self.state == new_state:
            return

        self.state = new_state
        self.iodriver.output_pin(self.pin, self.state)
        self.pub.forcepub()
        self.nvram.set_int(self.name, new_state)
        print("Switch %d = %d" % (self.pin, self.state))

    def is_on(self):
        return self.state
