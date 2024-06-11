import machine, os, os.path

singleton = None
ok = True

def test_mock():
    global ok
    f = machine.TEST_FOLDER + "mcp23017.sim"
    if not os.path.exists(f):
        return False
    print("Got mcp23017.sim")
    data = open(f).read().strip()
    os.remove(f)
    if data == 'fail':
        print("Simulate mcp23017 failure")
        ok = False
    elif data == 'good':
        print("Simulate mcp23017 restore")
        ok = True
    else:
        bitmap = int(data) & 0xffff
        print("Simulate mcp23017 gpio %x" % bitmap)
        singleton.porta._gpio, singleton.portb._gpio = bitmap >> 8, bitmap & 0xff
    return True

class Port:
    def __init__(self):
        self._gpio = 0
        self.pullup = 0
        self.mode = 0

    @property
    def gpio(self):
        if not ok:
            raise OSError()
        return self._gpio

    @gpio.setter
    def gpio(self, value):
        if not ok:
            raise OSError()
        self._gpio = value
        return value

class MCP23017:
    def __init__(self, i2c, port):
        if not ok:
            raise OSError()
        global singleton
        singleton = self
        self.porta = Port()
        self.portb = Port()
