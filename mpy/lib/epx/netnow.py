import network, machine, espnow, errno, os

from epx.loop import Task, MINUTES, SECONDS, MILISSECONDS
from epx import loop

broadcast_mac = const(b'\xff\xff\xff\xff\xff\xff')
version = 0x02
type_data = 0x01
type_announce = 0x02
signature = b'moo'

def mac_s2b(s):
    return bytes(int(x, 16) for x in s.split(':'))

def mac_b2s(mac):
    return ':'.join([f"{b:02X}" for b in mac])

class NetNowPeripheral:
    def __init__(self, cfg, nvram, watchdog):
        self.cfg = cfg
        self.nvram = nvram
        self.implnet = None
        self.impl = None
        self.active = False

        self.group = self.cfg.data['espnowgroup'].encode()

        startup_time = hasattr(machine, 'TEST_ENV') and 1 or (watchdog.grace_time() + 1)
        task = Task(False, "start", self.start, startup_time * SECONDS)

    def start(self, _):
        print("NetNowPeripheral: start")
        self.implnet = network.WLAN(network.STA_IF)
        self.implnet.active(False)
        self.implnet.active(True)

        self.impl = espnow.ESPNow()
        self.impl.active(True)
        self.active = True

        try:
            f = open("pair.txt")
            print("NetNowPeripheral: forced re-pairing")
            self.nvram.set_str('manager', '')
            f.close()
            os.unlink("pair.txt")
        except OSError:
            pass

        self.poll_task = Task(True, "poll", self.recv, 100 * MILISSECONDS)
        self.scan_task = None

        self.check_pairing()

    def check_pairing(self):
        manager = self.nvram.get_str('manager') or ""

        if not manager:
            print("NetNowPeripheral: not paired")
            self.paired = False
            self.manager = None
            self.channel = 0
            self.scan_task = Task(True, "scan", self.scan_channel, 5 * SECONDS)
            self.scan_task.advance()
            return

        if self.scan_task:
            self.scan_task.cancel()
            self.scan_task = None

        self.paired = True
        self.manager = mac_s2b(manager)
        self.channel = self.nvram.get_int('channel')
        self.impl.add_peer(self.manager)
        self.implnet.config(channel=self.channel)
        print("NetNowPeripheral: paired w/", manager, "channel", self.channel)

    def scan_channel(self, _):
        self.channel += 1
        if self.channel > 13:
            self.channel = 1
        self.implnet.config(channel=self.channel)
        print("NetNowPeripheral: now scanning channel",  self.channel)

    def recv(self, _):
        while self.impl.any():
            print("NetNowPeripheral: recv packet")
            mac, msg = self.impl.recv()
            self.handle_recv_packet(mac, msg)
    
    def handle_recv_packet(self, mac, msg):
        if len(msg) < 2:
            print("NetNowPeripheral.handle_recv_packet: invalid len")
            return
        if msg[0] != version:
            print("NetNowPeripheral.handle_recv_packet: unknown version", version)
            return
        if msg[1] == type_announce:
            self.handle_announce_packet(mac_b2s(mac), msg[2:])
            return
        print("NetNowPeripheral.handle_recv_packet: unknown type", msg[1])

    def handle_announce_packet(self, mac, msg):
        print("NetNowPeripheral: manager announced")
        if self.paired:
            print("...ignoring")
            return
        if len(msg) <= len(signature):
            print("...too short")
            return
        if msg[0:len(signature)] != signature:
            print("...invalid signature")
            return
        msg = msg[len(signature):]
        if msg != self.group:
            print("...not my group")
            return
        self.pair_with_manager(mac)

    def pair_with_manager(self, mac):
        print("NetworkPeripheral: pairing with", mac, "channel", self.channel)
        self.nvram.set_str('manager', mac)
        self.nvram.set_int('channel', self.channel)
        self.check_pairing()

    def send_data_unconfirmed(self, payload):
        if not self.manager:
            return False

        # first byte: version
        # second byte: packet type 
        buf = bytearray([version, type_data]) + payload
        self.impl.send(self.manager, buf, False)
        return True

    def send_data_confirmed(self, payload):
        if not self.manager:
            return False

        # first byte: version
        # second byte: packet type 
        buf = bytearray([version, type_data]) + payload
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
    def __init__(self, cfg, nvram, net):
        self.cfg = cfg
        self.nvram = nvram
        self.net = net
        self.impl = espnow.ESPNow()
        self.active = False
        self.data_recv_observers = []
        self.group = self.cfg.data['espnowgroup'].encode()

        self.net.observe("netnow", "connected", lambda: self.on_net_start())

    def on_net_start(self):
        print("NetNowManager: start")
        self.impl.active(True)
        self.active = True
        try:
            # must remove before re-adding
            self.impl.del_peer(broadcast_mac)
        except OSError:
            pass
        # must re-add, otherwise fails silently
        self.impl.add_peer(broadcast_mac)
        # did not use irq() since it interacted wierdly with our event loop
        # and it does not stop when program is interrupted

        self.poll_task = Task(True, "poll", self.recv, 100 * MILISSECONDS)
        self.pair_task = None
        self.announce_task = None

        self.net.observe("netnow", "connlost", lambda: self.on_net_stop())

    def on_net_stop(self):
        print("NetNowManager: stop")

        self.poll_task.cancel()
        if self.pair_task:
            self.pair_task.cancel()
            self.pair_task = None
        if self.announce_task:
            self.announce_task.cancel()
            self.announce_task = None

        self.impl.active(False)
        self.active = False
        self.net.observe("netnow", "connected", lambda: self.on_net_start())

    # Called e.g. when relevant MQTT topic is pinged
    def opentopair(self):
        if not self.active:
            return

        print("NetNowManager: open to pair")

        if self.pair_task:
            self.pair_task.cancel()
        if self.announce_task:
            self.announce_task.cancel()

        self.pair_task = Task(False, "pair", self.opentopair_end, 5 * MINUTES)
        self.announce_task = Task(True, "announce", self.announce, 500 * MILISSECONDS)
        # TODO close as soon as someone pairs

    def opentopair_end(self, _):
        print("NetNowManager: pair closed")
        if self.announce_task:
            self.announce_task.cancel()
            self.announce_task = None
        self.pair_task = None

    def announce(self, _):
        print("NetNowManager: announce")
        # TODO payload: nonce and psk
        buf = bytearray([version, type_announce]) + signature + self.group
        self.impl.send(broadcast_mac, buf, False)

    def register_recv_data(self, observer):
        if observer not in self.data_recv_observers:
            self.data_recv_observers.append(observer)

    def recv(self, _):
        while self.impl.any():
            print("NetNowManager: recv packet")
            mac, msg = self.impl.recv()
            self.handle_recv_packet(mac, msg)
    
    def handle_recv_packet(self, mac, msg):
        # TODO check whether mac is paired sensor saved in NVRAM
        # TODO maximum number of paired sensors
        if len(msg) < 2:
            print("NetNowManager.handle_recv_packet: invalid len")
            return
        if msg[0] != version:
            print("NetNowManager.handle_recv_packet: unknown version", version)
            return
        if msg[1] == type_data:
            self.handle_data_packet(mac_b2s(mac), msg[2:])
            return
        print("NetNowManager.handle_recv_packet: unknown type", msg[1])

    def handle_data_packet(self, smac, msg):
        for observer in self.data_recv_observers:
            observer.recv_data(smac, msg)
