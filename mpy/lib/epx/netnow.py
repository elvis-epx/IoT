import network, machine, espnow, errno, os
from hashlib import sha256

from epx.loop import MINUTES, SECONDS, MILISSECONDS, StateMachine
from epx import loop

broadcast_mac = const(b'\xff\xff\xff\xff\xff\xff')
version = const(0x02)
type_data = const(0x01)
type_announce = const(0x02)
type_pairreq = const(0x03)
type_pairaccept = const(0x04)
type_pairconfirm = const(0x05)
type_nonce = const(0x06)

def mac_s2b(s):
    return bytes(int(x, 16) for x in s.split(':'))

def mac_b2s(mac):
    return ':'.join([f"{b:02X}" for b in mac])

hash_size = const(12)

def gen_nonce():
    return os.urandom(hash_size)

def hash(data):
    h = sha256()
    h.update(data)
    return h.digest()[:hash_size]

def xor(a, b):
    if len(a) > len(b):
        a, b = b, a
    return bytes(x ^ y for x, y in zip(a, b)) + b[len(a):]

def hmac(key, data):
    return hash(xor(key, hash(xor(key, data))))

def check_hmac(key, data):
    return hmac(key, data[:-hash_size]) == data[-hash_size:]


class NetNowPeripheral:
    def __init__(self, cfg, nvram, watchdog):
        self.cfg = cfg
        self.nvram = nvram
        self.implnet = None
        self.impl = None

        self.group = self.cfg.data['espnowgroup'].encode()
        self.psk = self.cfg.data['espnowpsk'].encode()

        startup_time = hasattr(machine, 'TEST_ENV') and 1 or (watchdog.grace_time() + 1)

        sm = self.sm = StateMachine("netnowp")

        sm.add_state("start", self.on_start)
        sm.add_state("unpaired", self.on_unpaired)
        sm.add_state("paired", self.on_paired)

        sm.add_transition("initial", "start")
        sm.add_transition("start", "unpaired")
        sm.add_transition("start", "paired")
        sm.add_transition("unpaired", "paired")

        self.sm.schedule_trans("start", startup_time * SECONDS)

    def is_active(self):
        return self.sm.state == 'active' or self.sm.state == 'paired'

    def is_paired(self):
        return self.sm.state == 'paired'

    def on_start(self):
        print("NetNowPeripheral: start")
        self.implnet = network.WLAN(network.STA_IF)
        self.implnet.active(False)
        self.implnet.active(True)

        self.impl = espnow.ESPNow()
        self.impl.active(True)

        try:
            f = open("pair.txt")
            print("NetNowPeripheral: forced re-pairing")
            self.nvram.set_str('manager', '')
            f.close()
            os.unlink("pair.txt")
        except OSError:
            pass

        manager = self.nvram.get_str('manager') or ""
        if bool(manager):
            self.sm.schedule_trans_now("paired")
        else:
            self.sm.schedule_trans_now("unpaired")

    def active_tasks(self):
        self.sm.recurring_task("netnowp_poll", self.recv, 100 * MILISSECONDS)

    def on_unpaired(self):
        print("NetNowPeripheral: not paired")
        self.channel = 0
        tsk = self.sm.recurring_task("netnowp_scan", self.scan_channel, 5 * SECONDS)
        tsk.advance()
        self.active_tasks()

    def on_paired(self):
        manager = self.nvram.get_str('manager') or ""
        self.manager = mac_s2b(manager)
        self.channel = self.nvram.get_int('channel')
        self.impl.add_peer(self.manager)
        self.implnet.config(channel=self.channel)
        print("NetNowPeripheral: paired w/", manager, "channel", self.channel)
        self.active_tasks()

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
        if len(msg) < 18:
            print("NetNowPeripheral.handle_recv_packet: invalid len")
            return
        if msg[0] != version:
            print("NetNowPeripheral.handle_recv_packet: unknown version", version)
            return
        if not check_hmac(self.psk, msg):
            print("NetNowCentral.handle_recv_packet: bad hmac")
            return
        msg = msg[:-hash_size]
        if msg[1] == type_announce:
            self.handle_announce_packet(mac_b2s(mac), msg[2:])
            return
        print("NetNowPeripheral.handle_recv_packet: unknown type", msg[1])

    def handle_announce_packet(self, mac, msg):
        print("NetNowPeripheral: manager announced")
        if self.is_paired():
            print("...ignoring")
            return
        nonce, group = msg[:hash_size], msg[hash_size:]
        # TODO use nonce
        if group != self.group:
            print("...not my group")
            return
        self.pair_with_manager(mac)

    def pair_with_manager(self, mac):
        print("NetworkPeripheral: pairing with", mac, "channel", self.channel)
        self.nvram.set_str('manager', mac)
        self.nvram.set_int('channel', self.channel)
        self.sm.schedule_trans_now('paired')

    def send_data_unconfirmed(self, payload):
        if not self.is_paired():
            return False

        # first byte: version
        # second byte: packet type 
        buf = bytearray([version, type_data]) + payload
        buf += hmac(self.psk, buf)
        self.impl.send(self.manager, buf, False)
        return True

    def send_data_confirmed(self, payload):
        if not self.is_paired():
            return False

        # first byte: version
        # second byte: packet type 
        buf = bytearray([version, type_data]) + payload
        buf += hmac(self.psk, buf)
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


class NetNowCentral:
    def __init__(self, cfg, nvram, net):
        self.cfg = cfg
        self.nvram = nvram
        self.net = net
        self.impl = espnow.ESPNow()
        self.data_recv_observers = []

        self.group = self.cfg.data['espnowgroup'].encode()
        self.psk = self.cfg.data['espnowpsk'].encode()

        sm = self.sm = StateMachine("netnowc")

        sm.add_state("idle", self.on_idle)
        sm.add_state("active", self.on_active)
        sm.add_state("open", self.on_open)
        sm.add_state("inactive", self.on_inactive)

        sm.add_transition("initial", "idle")
        sm.add_transition("idle", "active")
        sm.add_transition("active", "open")
        sm.add_transition("open", "active")
        sm.add_transition("open", "inactive")
        sm.add_transition("active", "inactive")
        sm.add_transition("inactive", "idle")

        self.sm.schedule_trans_now("idle")

    def is_active(self):
        return self.sm.state == 'active' or self.sm.state == 'open'

    def is_open(self):
        return self.sm.state == 'open'

    def on_idle(self):
        self.net.observe("netnow", "connected", lambda: self.sm.schedule_trans_now("active"))

    def active_tasks(self):
        self.sm.recurring_task("netnowc_poll", self.recv, 100 * MILISSECONDS)
        self.net.observe("netnow", "connlost", lambda: self.sm.schedule_trans_now("inactive"))

    def on_active(self):
        print("NetNowCentral: active")
        self.impl.active(True)
        try:
            # must remove before re-adding
            self.impl.del_peer(broadcast_mac)
        except OSError:
            pass
        # must re-add, otherwise fails silently
        self.impl.add_peer(broadcast_mac)
        # did not use irq() since it interacted wierdly with our event loop
        # and it does not stop when program is interrupted
        self.active_tasks()

    def on_inactive(self):
        print("NetNowCentral: inactive")
        self.impl.active(False)
        self.sm.schedule_trans_now("idle")

    # Called e.g. when relevant MQTT topic is pinged
    def opentopair(self):
        self.sm.schedule_trans_now("open")
        
    def on_open(self):
        print("NetNowCentral: open to pair")
        self.active_tasks()
        self.pair_nonces = []
        self.sm.schedule_trans("close", 5 * MINUTES)
        self.sm.recurring_task("announce", self.announce, 500 * MILISSECONDS)

    def announce(self, _):
        print("NetNowCentral: announce")
        new_nonce = gen_nonce()
        self.pair_nonces = [ new_nonce ] + self.pair_nonces
        # Accept last 3 pair nonces announces
        self.pair_nonces = self.pair_nonces[:3]
        buf = bytearray([version, type_announce]) + new_nonce + self.group
        buf += hmac(self.psk, buf)
        self.impl.send(broadcast_mac, buf, False)

    def register_recv_data(self, observer):
        if observer not in self.data_recv_observers:
            self.data_recv_observers.append(observer)

    def recv(self, _):
        while self.impl.any():
            print("NetNowCentral: recv packet")
            mac, msg = self.impl.recv()
            self.handle_recv_packet(mac, msg)
    
    def handle_recv_packet(self, mac, msg):
        # TODO check whether mac is paired sensor saved in NVRAM
        # TODO maximum number of paired sensors
        # TODO accept pair requests only when open to pair
        # TODO close as soon as someone pairs
        if len(msg) < 18:
            print("NetNowCentral.handle_recv_packet: invalid len")
            return
        if msg[0] != version:
            print("NetNowCentral.handle_recv_packet: unknown version", version)
            return
        if not check_hmac(self.psk, msg):
            print("NetNowCentral.handle_recv_packet: bad hmac")
            return
        msg = msg[:-hash_size]
        if msg[1] == type_data:
            self.handle_data_packet(mac_b2s(mac), msg[2:])
            return
        print("NetNowCentral.handle_recv_packet: unknown type", msg[1])

    def handle_data_packet(self, smac, msg):
        for observer in self.data_recv_observers:
            observer.recv_data(smac, msg)
