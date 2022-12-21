import machine
from third import ssd1306
from epx.loop import Task, SECONDS, MILISSECONDS, Cronometer

RELAY_PINS = [25, 26, 27, 33]        # ESP32
INVERSE_LOGIC = const(1)             # some 3v3 Arduino relays
ON = const(1)
OFF = const(0)

class Relay:
    def __init__(self, number):
        self.name = "relay%d" % number
        self.number = number
        self.pin = machine.Pin(RELAY_PINS[number], machine.Pin.OUT)
        self.switch(OFF)
        self.auto_off = None

    def turn_on_with(self, timeout):
        if self.auto_off:
            self.auto_off.cancel()

        new_state = (timeout > 0) and ON or OFF
        self.switch(new_state)

        if not new_state:
            return
        print("\ttimeout in %d" % timeout)
        self.auto_off = Task(False, self.name, self.timeout, timeout * SECONDS)

    def timeout(self, _):
        self.switch(OFF)
        print("\ttimeout done")
        self.auto_off = None

    def switch(self, new_state):
        self.state = new_state and ON or OFF
        self.pin.value(new_state ^ INVERSE_LOGIC)
        print("Relay %d = %d" % (self.number, new_state))

    def is_on(self):
        return self.state


class Display:
    def __init__(self, i2c, relays, net, mqtt):
        try:
            self.impl = ssd1306.SSD1306_I2C(128, 64, i2c)
        except OSError:
            print("No display found")
            return

        self.relays = relays
        self.net = net
        self.mqtt = mqtt
        self.task = Task(True, "display", self.refresh, 500 * MILISSECONDS)
        self.blink = True
        self.uptime = Cronometer()

    def refresh(self, task):
        if not self.impl:
            task.cancel()
            print("Display task cancelled")
            return

        self.impl.fill(0)
        for i, relay in enumerate(self.relays):
            if self.relays[i].is_on() and self.blink:
                self.impl.fill_rect(0, i * 16, 12, 12, 1)
            else:
                self.impl.rect(0, i * 16, 12, 12, 1)
        self.blink = not self.blink

        netstatus, ifconfig = self.net.ifconfig()
        if ifconfig and netstatus == 'connected':
            self.impl.text(ifconfig[0][-8:], 20, 0)
        else:
            self.impl.text('no net', 20, 0)
        if self.mqtt.state() == 'connected':
            self.impl.text('MQTT up', 20, 12)
        else:
            self.impl.text('MQTT down', 20, 12)

        seconds = self.uptime.elapsed() // SECONDS
        minutes, seconds = seconds // 60, seconds % 60
        hours, minutes = minutes // 60, minutes % 60
        days, hours = hours // 24, hours % 24
        uptime = "%d:%02d:%02d:%02d" % (days, hours, minutes, seconds)

        self.impl.text(uptime, 20, 24)

        try:
            self.impl.show()
        except OSError:
            print("No display found")
            self.impl = None
