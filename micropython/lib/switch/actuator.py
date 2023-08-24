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

        self.state_in_nvram = self.nvram.get_int(self.name)
        self.switch(self.state_in_nvram)

    def switch(self, new_state):
        new_state = new_state and 1 or 0

        if self.state == new_state:
            return

        self.state = new_state
        self.iodriver.output_pin(self.pin, new_state)
        self.pub.forcepub()

        if self.state_in_nvram is None or self.state_in_nvram != new_state:
            self.nvram.set_int(self.name, new_state)

    def is_on(self):
        return self.state
