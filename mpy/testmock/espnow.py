import os
import os.path
import time
import socket
from select import select

import machine

singleton = None

recv_pkts = []

def test_mock():
    if not singleton:
        return False

    for f in sorted(os.listdir('espnow_packets/')):
        if not f.endswith(".rx"):
            continue
        rawdata = open("espnow_packets/" + f, "rb").read()
        os.unlink("espnow_packets/" + f)

        if len(rawdata) < 13:
            print("espnow mock: invalid packet")
            continue

        channel = int(rawdata[0])
        dmac = rawdata[1:7]
        smac = rawdata[7:13]
        data = rawdata[13:]

        if channel != machine._wifi.config('channel'):
            print("espnow mock: recv for channel I am not listening")
        elif dmac != singleton.my_mac and dmac != singleton.bcast_mac:
            print("espnow mock: recv for mac that is not me")
        else:
            recv_pkts.append((smac, data))
            singleton.pipe_w.send(b'p')
            return True

    return False

def clean_packets():
    try:
        os.mkdir('espnow_packets')
    except OSError as e:
        # Most probably existing folder
        pass

    for f in os.listdir('espnow_packets/'):
        os.unlink("espnow_packets/" + f)

def write_packet(data):
    f = "espnow_packets/%.9f.tx" % time.time()
    open(f, "wb").write(data)

class ESPNow:
    def __init__(self):
        clean_packets()

        f = "espnow_role"
        role = open(f).read().strip()
        if role == "central":
            self.my_mac = b"\x00\x01\x02\x03\x04\x05"
        elif role == "peripheral":
            self.my_mac = b"\x00\x01\x02\x03\x04\x05"
        else:
            raise Exception("Create espnow_role with proper content")
        self.bcast_mac = b"\xff\xff\xff\xff\xff\xff"
        self._active = False
        self.pipe_r, self.pipe_w = socket.socketpair()

        global singleton
        singleton = self

    def fileno(self):
        return self.pipe_r.fileno()

    def active(self, st):
        self._active = st

    def any(self):
        r, w, e = select([self.pipe_r], [], [], 0)
        return bool(r)

    def add_peer(self, mac):
        pass

    def del_peer(self, mac):
        pass

    def send(self, mac, data, confirmed):
        packet = bytes([machine._wifi.config('channel')]) + \
                mac + \
                self.my_mac + \
                data
        write_packet(packet)

    def recv(self):
        self.pipe_r.recv(1)
        smac, data = recv_pkts[0]
        recv_pkts = recv_pkts[1:]
        return smac, data
