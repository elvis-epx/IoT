from epx.loop import SECONDS, MINUTES, Task
from scale_manager.service import WeightPub, MalfunctionPub

class Forwarder():
    def __init__(self, cfg, netnow, mqtt):
        self.cfg = cfg
        self.netnow = netnow
        self.netnow.register_recv_data(self)

        self.wpub = mqtt.pub(WeightPub(self))
        self.mpub = mqtt.pub(MalfunctionPub(self))
        self._weight = None
        self._malfunction = None

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

        if data[0] == "stat/LPScale/Weight":
            try:
                self._weight = float(data[1])
            except ValueError:
                print("recv_data: invalid weight")
                return
            self.wpub.forcepub()
            return

        if data[0] == "stat/LPScale/Malfunction":
            try:
                self._malfunction = int(data[1], 10)
            except ValueError:
                print("recv_data: invalid malfunction value")
                return
            self.mpub.forcepub()
            return
            
        print("recv_data: unknown topic")

    def weight(self):
        return self._weight

    def malfunction(self):
        return self._malfunction
