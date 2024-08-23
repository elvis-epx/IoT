from epx.loop import SECONDS, MINUTES, Task, hibernate
import time, random

class Service():
    def __init__(self, cfg, watchdog, netnow):
        self.cfg = cfg
        self.netnow = netnow
        Task(False, "eval", self.eval, (watchdog.grace_time() + 2) * SECONDS)

    def eval(self, _):
        if not self.netnow.is_ready():
            Task(False, "eval", self.eval, 1 * SECONDS)
            return

        packet = "stat/TNow/Value\n%.1f" % random.random()
        self.netnow.send_data_unconfirmed(packet.encode())
