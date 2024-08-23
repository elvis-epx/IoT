from epx.loop import SECONDS, MINUTES, Task, hibernate
import random, os

class Service():
    def __init__(self, cfg, watchdog, netnow):
        self.cfg = cfg
        self.netnow = netnow
        Task(True, "eval", self.eval, 1 * SECONDS)

    def eval(self, _):
        if not self.netnow.is_ready():
            return

        try:
            f = open("tnowpsend.sim")
            f.close()
        except OSError:
            return

        os.unlink("tnowpsend.sim")

        packet = "stat/TNow/Value\n%d" % int(random.random() * 1000)
        self.netnow.send_data_unconfirmed(packet.encode())
