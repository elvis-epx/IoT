from epx.loop import SECONDS, MINUTES, Task
from tnowc.service import TNowPub

class Forwarder():
    def __init__(self, cfg, netnow, mqtt):
        self.cfg = cfg
        self.netnow = netnow
        self.netnow.register_recv_data(self)

        self.pub = mqtt.pub(TNowPub(self))
        self._value = None

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
            try:
                self._value = float(data[1])
            except ValueError:
                print("recv_data: invalid value")
                return
            self.pub.forcepub()
            return
            
        print("recv_data: unknown topic")

    def value(self):
        return self._value
