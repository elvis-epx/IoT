from epx.loop import Task, MINUTES, Shortcronometer
from third import mcp23017

# Proxy for access to MCP23017

class SerialIO:
    def __init__(self, i2c):
        self.i2c = i2c
        self.mcp = None
        self.malfunction_bitmap = 0
        self.input_bitmap = 0
        self.output_bitmap = 0
        Task(True, "mcpstart", self.start_mcp, 10 * MINUTES).advance()

    def start_mcp(self, _):
        if self.mcp:
            return

        try:
            self.mcp = mcp23017.MCP23017(self.i2c, 0x20)
            self.mcp.porta.mode = 0x00 # port A = output
            self.mcp.porta.pullup = 0x00
            self.mcp.portb.mode = 0xff # port B = input
            self.mcp.portb.pullup = 0xff
            self.malfunction_bitmap &= ~0x02
            print("serialio: mcp active")
        except OSError:
            print("serialio: mcp failed, retry in 10 min")
            self.fail(0x02)

    def eval(self):
        if not self.mcp:
            self.input_bitmap = 0
            return

        try:
            self.input_bitmap = self.mcp.portb.gpio
            self.mcp.porta.gpio = self.output_bitmap
            self.malfunction_bitmap &= ~0x01
        except OSError:
            print("serialio: mcp read fail")
            self.fail(0x01)

    def input(self):
        return self.input_bitmap

    def output(self, bitmap):
        self.output_bitmap = bitmap

    def input_pin(self, pin):
        return (self.input_bitmap & (1 << pin)) and 1 or 0

    def output_pin(self, pin, value):
        mask = 1 << pin
        if value:
            self.output_bitmap |= mask
        else:
            self.output_bitmap &= (~mask) & 0xff

    def fail(self, bit):
        self.mcp = None
        self.input_bitmap = 0
        self.malfunction_bitmap |= bit

    def malfunction(self):
        return self.malfunction_bitmap
