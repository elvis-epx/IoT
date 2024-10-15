import random, os, machine
from epx.loop import SECONDS, MINUTES, Task
from tnowc.service import TNowPub

class Forwarder():
    def __init__(self, cfg, netnow, mqtt):
        self.cfg = cfg
        self.netnow = netnow
        self.netnow.register_recv_data(self)

        self.pub = mqtt.pub(TNowPub(self))
        self._value = None

        if hasattr(machine, 'TEST_ENV'):
            Task(True, "eval", self.eval, 1 * SECONDS)
        else: # pragma: no cover
            Task(True, "eval", self.eval, 60 * SECONDS, 60 * SECONDS)

    def eval(self, _):
        if hasattr(machine, 'TEST_ENV'):
            try:
                f = open("tnowcsend.sim")
                f.close()
            except OSError:
                return
            os.unlink("tnowcsend.sim")

        packet = "stat/TNowP/Value\n%d" % int(random.random() * 1000)
        self.netnow.send_backdata(packet.encode())

    def recv_data(self, mac, data):
        print("Forwarder.recv_data")
        try:
            data = data.decode()
        except UnicodeError:
            print("recv_data: unicode error")
            return

        data = data.split('\n')
        if len(data) != 2:
            print("recv_data: split error")
            return

        if data[0] == "stat/TNow/Value":
            self._value = data[1]
            self.pub.forcepub()
            return
            
        print("recv_data: unknown topic")

    def value(self):
        return self._value
