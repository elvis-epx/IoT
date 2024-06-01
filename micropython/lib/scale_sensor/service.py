from epx.loop import SECONDS, MINUTES, Task, hibernate
import time

class Service():
    def __init__(self, cfg, netnow, sensor):
        self.cfg = cfg
        self.netnow = netnow
        self.sensor = sensor
        self.task = Task(True, "eval", self.eval, 30 * SECONDS)

    def eval(self, tsk):
        print("Service.eval")
        weight, malfunction = self.sensor.weight()
        if weight is None and malfunction is None:
            print("sensor not ready")
            return
        tsk.cancel()

        if weight is not None:
            packet = "stat/LPScale/Weight\n%.3f" % weight
        else:
            packet = "stat/LPScale/Malfunction\n%d" % malfunction

        print("Sending", packet)
        self.netnow.send_data_unconfirmed(packet.encode())
        Task(True, "stop", self.stop, 1 * SECONDS)

    def stop(self, _):
        print("Service.stop")
        self.sensor.disable()
        hibernate(30 * SECONDS)
        print("Service hibernated (should not print this...)")
        # FIXME test current consumption
