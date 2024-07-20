import machine
import os
import os.path
import socket

singleton = None

def test_mock():
    f = machine.TEST_FOLDER + "espnow.sim"
    if not os.path.exists(f):
        return False
    print("Got espnow.sim")
    cmd = open(f).read().strip()
    os.remove(f)
    if singleton._status > STAT_OFF:
        singleton._status = globals()["STAT_" + cmd]
    return True

class ESPNow:
    def __init__(self):
        global singleton
        singleton = self
        self._active = False
        self.sock_r, self.sock_w = socket.socketpair()

    def fileno(self):
        return self.sock_r.fileno()

    def active(self, st):
        self._active = st

    def any(self):
        return False

    def add_peer(self, mac):
        pass

    def del_peer(self, mac):
        pass

    def send(self, mac, data, confirmed):
        pass
