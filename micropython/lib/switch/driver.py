import machine
from machine import Pin

# Direct usage of GPIO pins in breadboard, input is complementary (1 = OFF)

class Direct4:
    def __init__(self):
        self.inputs = 4
        self.outputs = 4
        self.led = 2
        self.led_inverse = 0

        self.input_pins_no = [26, 34, 33, 35]
        self.output_pins_no = [17, 16, 32, 12]
        self.input_pins = [ Pin(n, Pin.IN) for n in self.input_pins_no ]
        self.output_pins = [ Pin(n, Pin.OUT) for n in self.output_pins_no ]

    def output_pin(self, pin, value):
        self.output_pins[pin].value(value)

    def input(self):
        bitmap = 0
        for i, pin in enumerate(self.input_pins):
            bitmap += (pin.value() and 1 or 0) << i
        return ~bitmap

# DTWonder www.dingtian-tech.com

class dtwonder2:
    def __init__(self):
        self.inputs = 2
        self.outputs = 2
        self.led = -1 # none
        self.led_inverse = 0

        self.input_pins_no = [36, 39]
        self.output_pins_no = [16, 2]
        self.input_pins = [ Pin(n, Pin.IN) for n in self.input_pins_no ]
        self.output_pins = [ Pin(n, Pin.OUT) for n in self.output_pins_no ]

    def output_pin(self, pin, value):
        self.output_pins[pin].value(value)

    def input(self):
        bitmap = 0
        for i, pin in enumerate(self.input_pins):
            bitmap += (pin.value() and 1 or 0) << i
        return ~bitmap

class dtwonder4:
    def __init__(self):
        self.inputs = 4
        self.outputs = 4
        self.led = -1 # none
        self.led_inverse = 0

        self.input_pins_no = [36, 39, 33, 35]
        self.output_pins_no = [16, 2, 32, 12]
        self.input_pins = [ Pin(n, Pin.IN) for n in self.input_pins_no ]
        self.output_pins = [ Pin(n, Pin.OUT) for n in self.output_pins_no ]

    def output_pin(self, pin, value):
        self.output_pins[pin].value(value)

    def input(self):
        bitmap = 0
        for i, pin in enumerate(self.input_pins):
            bitmap += (pin.value() and 1 or 0) << i
        return ~bitmap

# PLC HF-006 Hofffer Automação https://hofferautomacao.com/

class hoffer6:
    def __init__(self):
        self.inputs = 8
        self.outputs = 6
        self.led = 2
        self.led_inverse = 0

        self.input_pins_no = [36, 39, 32, 33, 25, 26, 27, 14]
        self.output_pins_no = [4, 16, 17, 18, 19, 23]
        self.input_pins = [ Pin(n, Pin.IN) for n in self.input_pins_no ]
        self.output_pins = [ Pin(n, Pin.OUT) for n in self.output_pins_no ]

    def output_pin(self, pin, value):
        self.output_pins[pin].value(value)

    def input(self):
        bitmap = 0
        for i, pin in enumerate(self.input_pins):
            bitmap += (pin.value() and 1 or 0) << i
        return bitmap
