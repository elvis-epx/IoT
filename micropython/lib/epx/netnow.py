import network, machine, espnow, errno

from epx.loop import Task, SECONDS, MINUTES
from epx import loop

def macparse(s):
    return bytes(int(x, 16) for x in s.split(':'))

def macencode(mac):
    return ':'.join([f"{b:02X}" for b in mac])

def sixteen(pwd):
    if not pwd:
        return pwd
    pwd = pwd * (1 + 16 // len(pwd))
    return pwd[0:16]

class NetNowPeripheral:
    def __init__(self, cfg):
        self.cfg = cfg
        self.implnet = None
        self.impl = None

        self.manager = macparse(self.cfg.data['manager'])
        if 'pmk' not in self.cfg.data:
            self.cfg.data['pmk'] = None
        self.cfg.data['pmk'] = sixteen(self.cfg.data['pmk'])
        if 'manager_lmk' not in self.cfg.data:
            self.cfg.data['manager_lmk'] = None
        self.cfg.data['manager_lmk'] = sixteen(self.cfg.data['manager_lmk'])

        # Delay startup to after the watchdog is active (10s)
        startup_time = hasattr(machine, 'TEST_ENV') and 1 or 12
        task = Task(False, "start", self.start, startup_time * SECONDS)

    def start(self, _):
        print("NetNowPeripheral: start")
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
        self.impl.send(self.manager, buf, False)

    def send_data_confirmed(self, payload):
        # first byte: version
        # second byte: packet type 
        buf = b'\x01' + b'\x01' + payload
        try:
            # return ESP-NOW inherent confirmation (retries up to 25ms)
            res = self.impl.send(self.manager, buf, True)
        except OSError as err:
            if err.errno == errno.ETIMEDOUT:
                # observed in tests
                res = False
            else:
                # should not happen
                raise
        return res


class NetNowManager:
    def __init__(self, cfg, net):
        self.cfg = cfg
        self.net = net
        self.impl = espnow.ESPNow()
        self.active = False
        self.data_recv_observers = []

        self.sensor = macparse(self.cfg.data['sensor'])
        if 'pmk' not in self.cfg.data:
            self.cfg.data['pmk'] = None
        self.cfg.data['pmk'] = sixteen(self.cfg.data['pmk'])
        if 'sensor_lmk' not in self.cfg.data:
            self.cfg.data['sensor_lmk'] = None
        self.cfg.data['sensor_lmk'] = sixteen(self.cfg.data['sensor_lmk'])

        self.net.observe("netnow", "connected", lambda: self.on_net_start())

    def on_net_start(self):
        print("NetNowManager: start")
        self.impl.active(True)
        self.active = True
        if self.cfg.data['pmk']:
            self.impl.set_pmk(self.cfg.data['pmk'])
        try:
            # must remove before re-adding
            self.impl.del_peer(self.sensor)
        except OSError:
            pass
        # must re-add, otherwise fails silently
        self.impl.add_peer(self.sensor, self.cfg.data['sensor_lmk'])

        # FIXME frequency?
        self.poll_task = Task(True, "recv_poll", self.recv, 1 * SECONDS)
        self.net.observe("netnow", "connlost", lambda: self.on_net_stop())
        # FIXME dupl?
        # self.impl.irq(self.recv)

    def on_net_stop(self):
        print("NetNowManager: stop")
        self.poll_task.cancel()
        self.impl.active(False)
        self.active = False
        self.net.observe("netnow", "connected", lambda: self.on_net_start())

    def register_recv_data(self, observer):
        if observer not in self.data_recv_observers:
            self.data_recv_observers.append(observer)

    def recv(self, _):
        print("NetNowManager: recv")
        while self.impl.any():
            mac, msg = self.impl.recv()
            self.sched_delivery(mac, msg)
    
    def sched_delivery(self, mac, msg):
        def deliver(_):
            self.handle_recv_packet(mac, msg)
        task = Task(False, "deferred_recv", deliver, 0)

    def handle_recv_packet(self, mac, msg):
        if mac != self.sensor:
            print("NetNowManager.handle_recv_packet: unknown peer")
            return
        if len(msg) < 2:
            print("NetNowManager.handle_recv_packet: invalid len")
            return
        if msg[0] != 0x01:
            print("NetNowManager.handle_recv_packet: unknown version")
            return
        if msg[1] == 0x01:
            self.handle_data_packet(macencode(mac), msg)
            return
        print("NetNowManager.handle_recv_packet: unknown type")

    def handle_data_packet(self, smac, msg):
        for observer in self.data_recv_observers:
            observer.recv_data(smac, msg[2:])
