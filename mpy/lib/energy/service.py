import machine
from epx.mqtt import MQTTPub, MQTTSub
from epx.loop import MILISSECONDS, SECONDS, MINUTES, Task, StateMachine


class Voltage(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/V", 0, 0, False)
        self.sensor = sensor
        self.sensor.pub_add(self)

    def gen_msg(self):
        if self.sensor.get_data('Vavg') is None:
            return None # pragma: no cover
        return "%.1f" % self.sensor.get_data('Vavg')

class VoltageMin(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/Vmin", 0, 0, False)
        self.sensor = sensor
        self.sensor.pub_add(self)

    def gen_msg(self):
        if self.sensor.get_data('Vmin') is None:
            return None # pragma: no cover
        return "%.1f" % self.sensor.get_data('Vmin')

class VoltageMax(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/Vmax", 0, 0, False)
        self.sensor = sensor
        self.sensor.pub_add(self)

    def gen_msg(self):
        if self.sensor.get_data('Vmax') is None:
            return None # pragma: no cover
        return "%.1f" % self.sensor.get_data('Vmax')


class Current(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/A", 0, 0, False)
        self.sensor = sensor
        self.sensor.pub_add(self)

    def gen_msg(self):
        if self.sensor.get_data('Aavg') is None:
            return None # pragma: no cover
        return "%.1f" % self.sensor.get_data('Aavg')

class CurrentMax(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/Amax", 0, 0, False)
        self.sensor = sensor
        self.sensor.pub_add(self)

    def gen_msg(self):
        if self.sensor.get_data('Amax') is None:
            return None # pragma: no cover
        return "%.1f" % self.sensor.get_data('Amax')


class Power(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/W", 0, 0, False)
        self.sensor = sensor
        self.sensor.pub_add(self)

    def gen_msg(self):
        if self.sensor.get_data('Wavg') is None:
            return None # pragma: no cover
        return "%.1f" % self.sensor.get_data('Wavg')


class PowerFactor(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/PowerFactor", 0, 0, False)
        self.sensor = sensor
        self.sensor.pub_add(self)

    def gen_msg(self):
        if self.sensor.get_data('pfavg') is None:
            return None # pragma: no cover
        return "%.2f" % self.sensor.get_data('pfavg')


class Malfunction(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/Malfunction", 5 * SECONDS, 30 * MINUTES, False)
        self.sensor = sensor

    def gen_msg(self):
        return "%d" % self.sensor.malfunction()
