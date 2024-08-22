from epx.loop import SECONDS, MINUTES, Task, hibernate
import time

class Service():
    def __init__(self, cfg, watchdog, netnow, sensor):
        self.cfg = cfg
        self.netnow = netnow
        self.sensor = sensor
        Task(False, "eval", self.eval, (watchdog.grace_time() + 2) * SECONDS)
        # maximum time to wait for sensor and network
        Task(False, "stop", self.stop, 5 * MINUTES)

    def eval(self, _):
        # print("Service.eval")

        if not self.netnow.is_ready():
            # print("network not ready")
            Task(False, "eval", self.eval, 1 * SECONDS)
            return

        weight, malfunction = self.sensor.weight()
        if weight is None and malfunction is None:
            # print("sensor not ready")
            Task(False, "eval", self.eval, 1 * SECONDS)
            return

        self.sensor.disable()
        if weight is not None:
            packet = "stat/LPScale/Weight\n%.1f" % weight
        else:
            packet = "stat/LPScale/Malfunction\n%d" % malfunction

        print("Sending", packet)
        self.netnow.send_data_unconfirmed(packet.encode())
        Task(False, "stop", self.stop, 1 * SECONDS)

    def stop(self, _):
        print("Service.stop")
        hibernate(60 * MINUTES)
