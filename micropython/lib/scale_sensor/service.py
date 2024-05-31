from epx.loop import SECONDS, MINUTES, Task, hibernate

class Service():
    def __init__(self, cfg, netnow, sensor):
        self.cfg = cfg
        self.netnow = netnow
        self.sensor = sensor
        self.task = Task(True, "eval", self.eval, 30 * SECONDS)

    def eval(self, tsk):
        weight, malfunction = self.sensor.weight()
        if weight is None and malfunction is None:
            # sensor not ready
            return
        tsk.cancel()

        if weight is not None:
            packet = "stat/LPScale/Weight\n%.3f" % weight
        else:
            packet = "stat/LPScale/Malfunction\n%d" % malfunction

        print("Sending", packet)
        if not netnow.send_data_unconfirmed(packet.encode()):
            print("Failed to send")

        self.sensor.disable()
        hibernate(60 * MINUTES)
