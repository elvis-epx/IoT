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

class VoltageNow(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/Vnow", 0, 0, False)
        self.sensor = sensor
        self.sensor.pub_now_add(self)

    def gen_msg(self):
        if self.sensor.get_data('V') is None:
            return None # pragma: no cover
        return "%.1f" % self.sensor.get_data('V')

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

class CurrentNow(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/Anow", 0, 0, False)
        self.sensor = sensor
        self.sensor.pub_now_add(self)

    def gen_msg(self):
        if self.sensor.get_data('A') is None:
            return None # pragma: no cover
        return "%.1f" % self.sensor.get_data('A')

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

class PowerNow(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/Wnow", 0, 0, False)
        self.sensor = sensor
        self.sensor.pub_now_add(self)

    def gen_msg(self):
        if self.sensor.get_data('W') is None:
            return None # pragma: no cover
        return "%.1f" % self.sensor.get_data('W')


class PowerFactor(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/PowerFactor", 0, 0, False)
        self.sensor = sensor
        self.sensor.pub_add(self)

    def gen_msg(self):
        if self.sensor.get_data('pfavg') is None:
            return None # pragma: no cover
        return "%.2f" % self.sensor.get_data('pfavg')

class PowerFactorNow(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/PFnow", 0, 0, False)
        self.sensor = sensor
        self.sensor.pub_now_add(self)

    def gen_msg(self):
        if self.sensor.get_data('pf') is None:
            return None # pragma: no cover
        return "%.2f" % self.sensor.get_data('pf')


class Malfunction(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/Malfunction", 5 * SECONDS, 30 * MINUTES, False)
        self.sensor = sensor

    def gen_msg(self):
        return "%d" % self.sensor.malfunction()


class Ticker(MQTTSub):
    def __init__(self, sensor):
        MQTTSub.__init__(self, "cmnd/%s/Ticker")
        self.sensor = sensor

    def recv(self, topic, msg, retained, dup):
        value = msg.lower().strip()
        if value in (b"on", b"1", b"up"):
            self.sensor.ticker(True)
        elif value in (b"off", b"0", b"down"):
            self.sensor.ticker(False)
