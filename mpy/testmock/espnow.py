import machine
import os
import os.path
from socket import *
from select import select

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
        f = machine.TEST_FOLDER + "espnow_role"
        role = open(f).read().strip()
        if role == "central":
            self.port_send = 12001
            self.port_recv = 12000
            self.my_mac = b"\x00\x01\x02\x03\x04\x05"
        elif role == "peripheral":
            self.port_send = 12000
            self.port_recv = 12001
            self.my_mac = b"\x00\x01\x02\x03\x04\x06"
        else:
            raise Exception("Create espnow_role with proper content")
        self.bcast_mac = b"\xff\xff\xff\xff\xff\xff"
        self._active = False
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", self.port_recv))

    def fileno(self):
        return self.sock.fileno()

    def active(self, st):
        self._active = st

    def any(self):
        r, w, e = select([self.sock], [], [], 0)
        return bool(r)

    def add_peer(self, mac):
        pass

    def del_peer(self, mac):
        pass

    def send(self, mac, data, confirmed):
        self.sock.sendto(mac + self.my_mac + data, ("127.0.0.1", self.port_send))

    def recv(self):
        rawdata, _ = self.sock.recvfrom(262)
        dmac = rawdata[0:6]
        smac = rawdata[6:12]
        data = rawdata[12:]
        if dmac != self.my_mac and dmac != self.bcast_mac:
            print("espnow mock: recv for mac that is not me")
        return smac, data
