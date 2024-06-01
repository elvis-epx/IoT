import network, machine, espnow

from epx.loop import Task, SECONDS, MINUTES
from epx import loop

def macparse(s):
    return bytes(int(x, 16) for x in mac.split(':'))

def macencode(mac):
    return ':'.join([f"{b:02X}" for b in mac])

class NetNowPeripheral:
    def __init__(self, cfg):
        self.cfg = cfg
        self.implnet = None
        self.impl = None

        self.manager = macparse(self.cfg.data['manager'])
        if 'pmk' not in self.cfg.data:
            self.cfg.data['pmk'] = None
        if 'manager_lmk' not in self.cfg.data:
            self.cfg.data['manager_lmk'] = None

        # Delay startup to after the watchdog is active (10s)
        startup_time = hasattr(machine, 'TEST_ENV') and 1 or 12
        task = Task(False, "start", self.start, startup_time * SECONDS)

    def start(self):
        self.implnet = network.WLAN(network.STA_IF)
        self.implnet.active(False)
        self.implnet.active(True)
        self.implnet.config(channel=int(self.cfg.data["channel"]))

        self.impl = espnow.ESPNow()
        self.impl.active(True)
        if self.cfg.data['pmk']:
            self.impl.set_pmk(self.cfg.data['pmk'])
        self.impl.add_peer(self.manager, self.cfg.data['manager_lmk'])

    def send_data_unconfirmed(self, payload):
        # first byte: version
        # second byte: packet type 
        buf = b'\x01' + b'\x01' + payload
        # return ESP-NOW inherent confirmation (retries up to 25ms)
        return self.impl.send(self.manager, buf)


class NetNowManager:
    def __init__(self, cfg, net):
        self.cfg = cfg
        self.net = net
        # FIXME need to recreate or can reuse?
        self.impl = espnow.ESPNow()
        self.impl.irq(self.recv)
        self.active = False
        self.data_recv_observers = []

        self.sensor = macparse(self.cfg.data['sensor'])
        if 'pmk' not in self.cfg.data:
            self.cfg.data['pmk'] = None
        if 'sensor_lmk' not in self.cfg.data:
            self.cfg.data['sensor_lmk'] = None

        self.net.observe("netnow", "connected", lambda: self.on_net_start())

    def on_net_start(self):
        print("NetNowManager: start")
        self.impl.active(True)
        self.active = True
        if self.cfg.data['pmk']:
            self.impl.set_pmk(self.cfg.data['pmk'])
        self.impl.add_peer(self.sensor, self.cfg.data['sensor_lmk'])

        self.net.observe("netnow", "connlost", lambda: self.on_net_stop())

    def on_net_stop(self):
        print("NetNowManager: stop")
        self.impl.active(False)
        self.active = False
        self.net.observe("netnow", "connected", lambda: self.on_net_start())

    def register_recv_data(self, observer):
        if observer not in self.data_recv_observers:
            self.data_recv_observers.append(observer)

    def recv(self, e):
        while e.any():
            mac, msg = e.recv()
            self.sched_delivery(mac, msg)
    
    def sched_delivery(self, mac, msg):
        def deliver():
            self.handle_recv_packet(mac, msg)
        task = Task(False, "recv", deliver, 0)

    def handle_recv_packet(self, mac, msg):
        if mac != self.sensor:
            print("recv_packet: unknown peer")
            return
        if len(msg) < 2:
            print("recv_packet: invalid len")
            return
        if msg[0] != 0x01:
            print("recv_packet: unknown version")
            return
        if msg[1] == 0x01:
            self.handle_data_packet(macencode(mac), msg)
            return
        print("recv_packet: unknown type")

    def handle_data_packet(self, smac, msg):
        for observer in self.data_recv_observers:
            observer.recv_data(smac, msg[2:])
