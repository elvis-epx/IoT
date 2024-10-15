from epx.loop import SECONDS, MINUTES, Task, hibernate
import random, os, machine

class Service():
    def __init__(self, cfg, watchdog, netnow):
        self.cfg = cfg
        self.netnow = netnow
        self.netnow.register_recv_data(self)
        if hasattr(machine, 'TEST_ENV'):
            Task(True, "eval", self.eval, 1 * SECONDS)
        else: # pragma: no cover
            Task(True, "eval", self.eval, 15 * SECONDS, 15 * SECONDS)

    def eval(self, _):
        cmode = 0
        if hasattr(machine, 'TEST_ENV'):
            try:
                f = open("tnowpsend.sim")
                mode = f.read().strip()
                if "confirm" in mode:
                    cmode = 1
                f.close()
            except OSError:
                return
            os.unlink("tnowpsend.sim")

        packet = "stat/TNow/Value\n%d" % int(random.random() * 1000)
        self.netnow.send_data(packet.encode(), confirm_mode=cmode)

    def recv_data(self, tid, msg):
        print("Received back data", msg)
