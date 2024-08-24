from epx.loop import SECONDS, MINUTES, Task, hibernate
import random, os

class Service():
    def __init__(self, cfg, watchdog, netnow):
        self.cfg = cfg
        self.netnow = netnow
        Task(True, "eval", self.eval, 1 * SECONDS)

    def eval(self, _):
        try:
            f = open("tnowpsend.sim")
            f.close()
        except OSError:
            return

        os.unlink("tnowpsend.sim")

        packet = "stat/TNow/Value\n%d" % int(random.random() * 1000)
        self.netnow.send_data(packet.encode(), confirm_mode=0)
