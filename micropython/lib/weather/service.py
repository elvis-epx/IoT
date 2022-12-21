from epx.mqtt import MQTTPub, MQTTSub
from epx.loop import Cronometer, SECONDS, MINUTES

class Temperature(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/Temperature", 60 * SECONDS, 30 * MINUTES, False)
        self.sensor = sensor

    def gen_msg(self):
        # as float
        if self.sensor.temperature() is None:
            return None
        return "%.1f" % self.sensor.temperature()


class Humidity(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/Humidity", 60 * SECONDS, 30 * MINUTES, False)
        self.sensor = sensor

    def gen_msg(self):
        # as float but not very precise
        if self.sensor.humidity() is None:
            return None
        return "%.1f" % self.sensor.humidity()


class Pressure(MQTTPub):
    def __init__(self, sensor):
        # as float (hPa)
        MQTTPub.__init__(self, "stat/%s/Pressure", 60 * SECONDS, 30 * MINUTES, False)
        self.sensor = sensor

    def gen_msg(self):
        if self.sensor.pressure() is None:
            return None
        return "%.1f" % self.sensor.pressure()


class Malfunction(MQTTPub):
    def __init__(self, sensor):
        # as integer (bitmap)
        MQTTPub.__init__(self, "stat/%s/Malfunction", 60 * SECONDS, 30 * MINUTES, False)
        self.sensor = sensor

    def gen_msg(self):
        return "%d" % self.sensor.malfunction()


