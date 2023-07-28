import machine
from third import ssd1306
from epx.loop import Task, SECONDS, MILISSECONDS, Longcronometer

INVERSE_LOGIC = const(1)             # some 3v3 Arduino switches
ON = const(1)
OFF = const(0)

class Switch:
    def __init__(self, name, gpio, pin, inputmode, switchmode, manual):
        self.name = name
        self.gpio = gpio
        self.pin = pin
        self.manual = manual
        self.inputmode = inputmode
        self.switchmode = switchmode

        if self.switchmode == 'mem':
            # FIXME NVRAM state
            pass
        self.switch(OFF)
        self.manual.register_switch(self)

    def switch(self, new_state):
        self.state = new_state and ON or OFF
        self.gpio.output_pin(self.pin, new_state ^ INVERSE_LOGIC)
        print("Switch %s = %d" % (self.name, new_state))
        if self.switchmode == 'mem':
            # FIXME NVRAM support x mode 'mem'
            pass

    def toggle(self):
        if self.state:
            self.switch(OFF)
        else:
            sself.switch(ON)

    def is_on(self):
        return self.state


class Display:
    def __init__(self, i2c, switches, net, mqtt):
        try:
            self.impl = ssd1306.SSD1306_I2C(128, 64, i2c)
        except OSError:
            print("No display found")
            return

        self.switches = switches
        self.net = net
        self.mqtt = mqtt
        self.task = Task(True, "display", self.refresh, 500 * MILISSECONDS)
        self.blink = True
        self.uptime = Longcronometer()

    def refresh(self, task):
        if not self.impl:
            task.cancel()
            print("Display task cancelled")
            return

        self.impl.fill(0)
        names = list(self.switches.keys())
        names.sort()
        for name in names:
            if self.switches[name].is_on() and self.blink:
                self.impl.fill_rect(0, i * 8, 12, 12, 1)
            else:
                self.impl.rect(0, i * 8, 12, 12, 1)
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
