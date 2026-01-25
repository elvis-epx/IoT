from machine import Pin
import time

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

    def start(self):
        pass


# DTWonder www.dingtian-tech.com

class dtwonder2: # pragma: no cover
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

    def start(self):
        pass

# DTWonder debug port pins:
# GND
# IO3 = UART RX
# IO1 = UART TX
# NRST (ground to reset)
# IO0 (ground when resetting to put in bootloader mode)
# 3.3V

class dtwonder4: # pragma: no cover
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

    def start(self):
        pass


# PLC HF-006 Hofffer Automação https://hofferautomacao.com/

class hoffer6: # pragma: no cover
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

    def start(self):
        pass


# Sonoff Mini R4 (yes, it can run MicroPython)

class minir4: # pragma: no cover
    def __init__(self):
        self.inputs = 2
        self.outputs = 1
        self.led = 19
        self.led_inverse = 1

        # External box button = GPIO 0
        # Manual input = GPIO 27
        # Short-circuit S1 and S2 = actuate manual input
        self.input_pins_no = [27, 0]
        self.output_pins_no = [26]
        self.input_pins = [ Pin(n, Pin.IN) for n in self.input_pins_no ]
        self.output_pins = [ Pin(n, Pin.OUT) for n in self.output_pins_no ]

    def output_pin(self, pin, value):
        self.output_pins[pin].value(value)

    def input(self):
        bitmap = 0
        for i, pin in enumerate(self.input_pins):
            bitmap += (pin.value() and 1 or 0) << i
        return ~bitmap

    def start(self):
        pass


# DTWonder www.dingtian-tech.com with 8 inputs and 8 outputs

class dtwonder8: # pragma: no cover
    def __init__(self):
        self.inputs = 8
        self.outputs = 8
        self.led = -1 # none
        self.led_inverse = 0

        # pin 13 (/OE) of '595
        self.output_enable = Pin(32, Pin.OUT)
        # pin 12 (RCLK) of '595 and pin 15 (CLK_INH) of '165
        self.clock_inhibit = Pin(15, Pin.OUT)
        # pin 11 (SRCLK) of '595 and pin 2 (CLK) of '165
        self.clock = Pin(14, Pin.OUT)
        # pin 9 (QH) of '165
        self.bit_in = Pin(16, Pin.IN)
        # pin 14 (SER) of '595
        self.bit_out = Pin(13, Pin.OUT)

        # disable all relays until first I/O is done
        # (commented out to avoid flickering relays at warm restart)
        # self.output_enable.value(1)

        # Rest values
        self.clock_inhibit.value(1)
        self.clock.value(0)

        self.output_bitmap = 0
        # Wait until all switches fill in their virtual pins to fill 74LS bitmap
        # (prevents flickering relays at warm restart)
        self.started = False

    def output_pin(self, pin, value):
        if value:
            self.output_bitmap |= (1 << pin)
        else:
            self.output_bitmap &= ~(1 << pin)
        if self.started:
            self.do_io()

    def start(self):
        self.started = True
        self.do_io()

    def input(self):
        return (~self.do_io()) & 0xff

    # Read 74HC165 and write 74HC595
    # (they are tied together, so they need to be read and written at the same time)
    # It seems that SH/LD of the '165 is tied together with CLK INH, so we don't need
    # to operate this pin separately

    def do_io(self):
        input_bitmap = 0

        # start transaction
        time.sleep_us(1)
        self.clock_inhibit.value(0)
        time.sleep_us(1)

        for bit in range(0, 8):
            # Read bit from 165 and write bit to 595
            # LSB first
            input_bitmap |= (self.bit_in.value() and 1 or 0) << bit
            # MSB first, but DTWonder defines MSB0 = relay 1, so LSB too
            self.bit_out.value((self.output_bitmap & (1 << bit)) and 1 or 0)

            # Pulse clock to load 595 and shift 165
            time.sleep_us(1)
            self.clock.value(1)
            time.sleep_us(1)
            self.clock.value(0)
            time.sleep_us(1)

        # end transaction
        time.sleep_us(1)
        self.clock_inhibit.value(1)

        # enable relays
        time.sleep_us(1)
        self.output_enable.value(0)

        return input_bitmap
