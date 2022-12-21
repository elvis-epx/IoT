from third import ssd1306
from epx.loop import Task, SECONDS, MILISSECONDS, Cronometer

class Display:
    def __init__(self, config, i2c, net, mqtt, levelmeter, flowmeter):
        try:
            self.impl = ssd1306.SSD1306_I2C(128, 64, i2c)
        except OSError:
            print("No display found")
            return

        self.unit = config.data['unit']
        self.net = net
        self.mqtt = mqtt
        self.levelmeter = levelmeter
        self.flowmeter = flowmeter
        self.task = Task(True, "display", self.refresh, 1000 * MILISSECONDS)
        self.uptime = Cronometer()
        self.blink = False

    def refresh(self, task):
        if not self.impl:
            task.cancel()
            print("Display task cancelled")
            return

        flowrate = self.flowmeter.rate()
        m = self.levelmeter.malfunction()

        self.impl.fill(0)

        self.blink = not self.blink
        if flowrate <= 0.0 or self.blink:
            w = m and 6 or 12
            self.impl.rect(0, 0, 12, 63, 1)
            vol_pct = self.levelmeter.coarse_level_pct()
            if vol_pct is not None:
                self.impl.fill_rect(0, 63 - int(62.0 * vol_pct / 100.0), w, 63, 1)

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

        if m:
            s = "Error %d" % m
        else:
            s = self.levelmeter.estimated_level_str()
            s = s or ""
        self.impl.text(s, 20, 36)

        if flowrate > 0.0:
            flowrate = "%.1f%s/min" % (flowrate, self.unit)
        else:
            flowrate = "No flow"
        self.impl.text(flowrate, 20, 48)

        try:
            self.impl.show()
        except OSError:
            print("No display found")
            self.impl = None
