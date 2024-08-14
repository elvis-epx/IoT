from third import ssd1306
from epx.loop import Task, SECONDS, MILISSECONDS, Longcronometer

class Display:
    def __init__(self, config, i2c, sensor):
        try:
            self.impl = ssd1306.SSD1306_I2C(128, 64, i2c)
        except OSError: # pragma: no cover
            print("No display found")
            return

        self.task = Task(True, "display", self.refresh, 5000 * MILISSECONDS)
        self.uptime = Longcronometer()
        self.sensor = sensor

    def refresh(self, task):
        if not self.impl:
            task.cancel()
            print("Display task cancelled")
            return

        self.impl.fill(0)

        seconds = self.uptime.elapsed() // SECONDS
        minutes, seconds = seconds // 60, seconds % 60
        hours, minutes = minutes // 60, minutes % 60
        days, hours = hours // 24, hours % 24
        uptime = "%d:%02d:%02d:%02d" % (days, hours, minutes, seconds)
        self.impl.text(uptime, 20, 0)

        t = self.sensor.temperature()
        if t is not None:
            self.impl.text("%.1f C" % t, 20, 12)
        h = self.sensor.humidity()
        if h is not None:
            self.impl.text("%.1f %%" % h, 20, 24)
        p = self.sensor.pressure()
        if p is not None:
            self.impl.text("%.1f hPa" % p, 20, 36)
        if p is not None and t is not None:
            # h = (((1013.0 / p) ** (1 / 5.257) - 1) * (20 + 273.15)) / 0.0065
            h = (((1013.0 / p) ** (1 / 5.257) - 1) * (t + 273.15)) / 0.0065
            self.impl.text("%.2f m" % h, 20, 48)
        try:
            self.impl.show()
        except OSError: # pragma: no cover
            print("No display found")
            self.impl = None
