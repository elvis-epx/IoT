import machine
from epx.mqtt import MQTTPub, MQTTSub
from epx.loop import MILISSECONDS, SECONDS, MINUTES, Task, StateMachine


class Voltage(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/V", 0, 60 * SECONDS, False)
        self.sensor = sensor

    def gen_msg(self):
        # as float
        if self.sensor.voltage() is None:
            return None
        return "%.1f" % self.sensor.voltage()


class Current(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/A", 0, 60 * SECONDS, False)
        self.sensor = sensor

    def gen_msg(self):
        # as float
        if self.sensor.current() is None:
            return None
        return "%.1f" % self.sensor.current()


class Power(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/W", 0, 60 * SECONDS, False)
        self.sensor = sensor

    def gen_msg(self):
        # as float
        if self.sensor.power() is None:
            return None
        return "%.1f" % self.sensor.power()



class PowerFactor(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/PowerFactor", 0, 60 * SECONDS, False)
        self.sensor = sensor

    def gen_msg(self):
        # as float
        if self.sensor.powerfactor() is None:
            return None
        return "%.2f" % self.sensor.powerfactor()


class Energy(MQTTPub):
    def __init__(self, sensor):
        MQTTPub.__init__(self, "stat/%s/Wh", 0, 0, False)
        # published when sensor says so
        self.sensor = sensor
        sensor.register_energy_observer(self)

    def please_publish(self):
        # called by sensor at the end of energy accumulation time
        self.forcepub()

    def gen_msg(self):
        # as float, though PZEM supplies Wh as integer
        if self.sensor.energy() is None:
            return None # pragma: no cover
        return "%.1f" % self.sensor.energy()


class Malfunction(MQTTPub):
    def __init__(self, sensor):
        # as integer (bitmap)
        MQTTPub.__init__(self, "stat/%s/Malfunction", 5 * SECONDS, 30 * MINUTES, False)
        self.sensor = sensor

    def gen_msg(self):
        return "%d" % self.sensor.malfunction()


if hasattr(machine, 'TEST_ENV'):
    import socket
    sockerror = (IOError,)
    def setuplistener(s):
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
else: # pragma: no cover
    import usocket as socket
    sockerror = (OSError,)
    def setuplistener(s):
        pass

class Ticker:
    def __init__(self, sensor):
        self.sensor = sensor

        self.sock = socket.socket()
        self.sock.setblocking(False)
        setuplistener(self.sock)
        self.sock.bind(('0.0.0.0', 1338))
        self.sock.listen(1)

        sm = self.sm = StateMachine("ticker")

        sm.add_state("listen", self.on_listen)
        sm.add_state("connected", self.on_connected)
        sm.add_state("senddata", self.on_senddata)
        sm.add_state("connlost", self.on_connlost)

        sm.add_transition("initial", "listen")
        sm.add_transition("listen", "connected")
        sm.add_transition("connected", "senddata")
        sm.add_transition("senddata", "connected")
        sm.add_transition("senddata", "connlost")
        sm.add_transition("connlost", "listen")
        
        self.connection = None

        self.sm.schedule_trans("listen", 30 * SECONDS)

    def on_listen(self):
        if self.connection:
            self.connection.close()
            self.connection = None
        self.sm.recurring_task("ticker_listen", self.listen_poll, 500 * MILISSECONDS)

    def listen_poll(self, _):
        try:
            self.connection, _ = self.sock.accept()
        except sockerror as e:
            # could be EAGAIN or not, either case, can't do anything about
            return
        self.connection.setblocking(False)
        self.sm.schedule_trans_now("connected")

    def on_connected(self):
        self.sm.schedule_trans("senddata", 2 * SECONDS)

    def on_senddata(self):
        s = self.sensor.jsonish().encode()
        try:
            n = self.connection.send(s)
            if n <= 0: # pragma: no cover
                # difficult to happen or rehearse; output buffer is full
                # or the remote party called shutdown(SHUT_RD).
                self.sm.schedule_trans_now("connlost")
                return
        except sockerror as e:
            self.sm.schedule_trans_now("connlost")
            return
        self.sm.schedule_trans_now("connected")

    def on_connlost(self):
        self.sm.schedule_trans_now("listen")
