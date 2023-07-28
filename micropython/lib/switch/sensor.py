from epx.loop import Task, SECONDS, MINUTES
from epx import loop

INVERSE_LOGIC = const(1)

class Manual:
    def __init__(self, name, gpio, pin, inputmode, switchmode):
        self.name = name
        self.switch = None
        self.gpio = gpio
        self.pin = pin
        self.inputmode = inputmode
        self.switchmode = switchmode

        self.current = -1
        self.next = -1
        self.debounce = 0

    def register_switch(self, switch):
        self.switch = switch

    def eval(self):
        bit = self.gpio.input_pin(self.pin) ^ INVERSE_LOGIC
        if bit == self.current:
            # no change
            self.debounce = 0
            return

        if self.debounce == 0:
            # change detected, first pass
            self.next = bit
            self.debounce = 1
            return

        if bit != self.next:
            # flaky, restart
            self.debounce = 0

        # Change committed
        self.current = bit
        self.debounce = 0
        
        # Currently, only implement pulse switch
        if self.current:
            # Pulsed, toggle switch
            if self.switch:
                self.switch.toggle()
