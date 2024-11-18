from epx.mqtt import MQTTPub
from epx.loop import MILISSECONDS, SECONDS, MINUTES, Shortcronometer, Longcronometer


class KeyfobService(MQTTPub):
    def __init__(self):
        # client must call forcepub() manually
        MQTTPub.__init__(self, "stat/%s/Keyfob", 0, 0, False)
        self.value = None
        self.last_update = Shortcronometer()

    def new_value(self, value):
        if self.last_update.elapsed() < (250 * MILISSECONDS):
            return
        self.value = value
        self.forcepub()
        self.last_update.restart()

    def gen_msg(self):
        return self.value


class KeyfobStats(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/Statistics", 10 * MINUTES, 10 * MINUTES, False)
        self.sensor = sensor

    def gen_msg(self):
        return self.sensor.stats()
