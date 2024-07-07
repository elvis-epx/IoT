import network, machine, espnow, errno, os
from hashlib import sha256

from epx.loop import MINUTES, SECONDS, MILISSECONDS, StateMachine, Shortcronometer
from epx import loop

broadcast_mac = const(b'\xff\xff\xff\xff\xff\xff')
version = const(0x02)

type_data = const(0x01)

type_nettime = const(0x02)
nettime_subtype_default = const(0x00)
nettime_subtype_open = const(0x01)
nettime_subtype_confirm = const(0x02)

type_pair = const(0x03)

def mac_s2b(s):
    return bytes(int(x, 16) for x in s.split(':'))

def mac_b2s(mac):
    return ':'.join([f"{b:02X}" for b in mac])

def b2s(data):
    return ':'.join([f"{b:02X}" for b in data])

group_size = const(8)
hmac_size = const(12)

def gen_nonce():
    return os.urandom(hmac_size)

def hash(data):
    h = sha256()
    h.update(data)
    return h.digest()

def group_hash(group):
    return hash(group)[0:group_size]

def xor(a, b):
    if len(a) > len(b):
        a, b = b, a
    return bytes(x ^ y for x, y in zip(a, b)) + b[len(a):]

def hmac(key, data):
    return hash(xor(key, hash(xor(key, data))))[:hmac_size]

def check_hmac(key, data):
    return hmac(key, data[:-hmac_size]) == data[-hmac_size:]


class NetNowPeripheral:
    def __init__(self, cfg, nvram, watchdog):
        self.cfg = cfg
        self.nvram = nvram
        self.implnet = None
        self.impl = None
        self.current_nettime = None
        self.tids = {}

        self.group = group_hash(self.cfg.data['espnowgroup'].encode())
        self.psk = self.cfg.data['espnowpsk'].encode()

        startup_time = hasattr(machine, 'TEST_ENV') and 1 or (watchdog.grace_time() + 1)

        sm = self.sm = StateMachine("netnowp")

        sm.add_state("start", self.on_start)
        sm.add_state("unpaired", self.on_unpaired)
        sm.add_state("pairing", self.on_pairing)
        sm.add_state("paired", self.on_paired)

        sm.add_transition("initial", "start")
        sm.add_transition("start", "unpaired")
        sm.add_transition("start", "paired")
        sm.add_transition("unpaired", "pairing")
        sm.add_transition("pairing", "paired")
        sm.add_transition("pairing", "unpaired")

        self.sm.schedule_trans("start", startup_time * SECONDS)

    def is_ready(self):
        return self.sm.state == 'paired' and self.current_nettime is not None

    def on_start(self):
        self.implnet = network.WLAN(network.STA_IF)
        self.implnet.active(False)
        self.implnet.active(True)

        self.impl = espnow.ESPNow()
        self.impl.active(True)
        self.current_nettime = None

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

    def common_tasks(self):
        self.sm.recurring_task("netnowp_poll", self.recv, 100 * MILISSECONDS)

    def on_unpaired(self):
        self.channel = 0
        tsk = self.sm.recurring_task("netnowp_scan", self.scan_channel, 5 * SECONDS)
        tsk.advance()
        self.common_tasks()

    def on_pairing(self):
        print("NetworkPeripheral: pairing with", mac_b2s(self.manager), "channel", self.channel)
        self.sm.schedule_trans("unpaired", 5 * MINUTES)
        tsk = self.sm.recurring_task("netnowp_reqpair", self.send_pairreq, 5 * SECONDS)
        tsk.advance()
        self.common_tasks()

    def on_paired(self):
        manager = self.nvram.get_str('manager') or ""
        self.manager = mac_s2b(manager)
        self.channel = self.nvram.get_int('channel')
        self.impl.add_peer(self.manager)
        self.implnet.config(channel=self.channel)
        print("NetNowPeripheral: paired w/", manager, "channel", self.channel)
        self.common_tasks()

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
        if len(msg) < 2 + hmac_size:
            print("NetNowPeripheral.handle_recv_packet: invalid len")
            return
        if msg[0] != version:
            print("NetNowPeripheral.handle_recv_packet: unknown version", version)
            return
        if not check_hmac(self.psk, msg):
            print("NetNowCentral.handle_recv_packet: bad hmac")
            return
        pkttype = msg[1]
        msg = msg[2:-hmac_size]
        if pkttype == type_nettime:
            self.handle_nettime(mac_b2s(mac), msg)
            return
        print("NetNowPeripheral.handle_recv_packet: unknown type", pkttype)

    def handle_nettime(self, mac, msg):
        print("NetNowPeripheral: nettime")
        if len(msg) < (group_size+1+hmac_size):
            print("... invalid len")
            return

        subtype = msg[0]
        group = msg[1:group_size+1]

        if group != self.group:
            print("...not my group")
            return

        nettime = msg[group_size+1:group_size+1+hmac_size]
        self.current_nettime = nettime

        if subtype == nettime_subtype_open:
            if self.sm.state == 'unpaired':
                self.manager = mac_s2b(mac)
                self.sm.schedule_trans_now("pairing")
            return

        if subtype == nettime_subtype_confirm:
            if len(msg) != (group_size+1+hmac_size+hmac_size):
                print("... invalid confirm len")
                return
            tid = msg[group_size+1+hmac_size:]
            self.tid_confirm(tid)
            return

    def tid_cleanup(self):
        for tid in list(self.tids.keys()):
            if self.tids[tid]["crono"].elapsed() > self.tids[tid]["timeout"]:
                del self.tids[tid]

    def tid_confirm(self, tid):
        if tid in self.tids:
            print("confirm", b2s(tid))
            self.tids[tid]["cb"]()
            del self.tids[tid]
        self.tid_cleanup()

    def on_tid_confirm(self, timeout, tid, cb):
        self.tids[tid] = {"crono": Shortcronometer(), "timeout": timeout, "cb": cb}
        self.tid_cleanup()

    def send_pairreq(self):
        tid = gen_nonce()
        buf = bytearray([version, type_pair])
        buf += self.current_nettime 
        buf += tid
        buf += hmac(self.psk, buf)
        self.impl.send(self.manager, buf, False)
        print("sent pair tid", b2s(tid))

        def pairreq_confirmed():
            self.nvram.set_str('manager', mac_b2s(self.manager))
            self.nvram.set_int('channel', self.channel)
            self.sm.schedule_trans_now('paired')

        self.on_tid_confirm(5 * SECONDS, tid, pairreq_confirmed)

    # TODO refactor to use on_tid_confirm

    def send_data_unconfirmed(self, payload):
        if not self.is_ready():
            return False

        tid = gen_nonce()
        buf = bytearray([version, type_data])
        buf += self.current_nettime 
        buf += tid
        buf += payload
        buf += hmac(self.psk, buf)
        self.impl.send(self.manager, buf, False)
        print("sent tid", b2s(tid))
        return True

    def send_data_confirmed(self, payload):
        if not self.is_ready():
            return False

        tid = gen_nonce()
        buf = bytearray([version, type_data])
        buf += self.current_nettime 
        buf += tid
        buf += payload
        buf += hmac(self.psk, buf)
        try:
            # return ESP-NOW inherent confirmation (retries up to 25ms)
            res = self.impl.send(self.manager, buf, True)
            print("sent tid", b2s(tid))
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

        self.group = group_hash(self.cfg.data['espnowgroup'].encode())
        self.psk = self.cfg.data['espnowpsk'].encode()

        sm = self.sm = StateMachine("netnowc")

        sm.add_state("idle", self.on_idle)
        sm.add_state("active", self.on_active)
        sm.add_state("closed", self.on_closed)
        sm.add_state("open", self.on_open)
        sm.add_state("inactive", self.on_inactive)

        sm.add_transition("initial", "idle")
        sm.add_transition("idle", "active")
        sm.add_transition("active", "closed")
        sm.add_transition("closed", "open")
        sm.add_transition("closed", "inactive")
        sm.add_transition("open", "closed")
        sm.add_transition("open", "inactive")
        sm.add_transition("inactive", "idle")

        self.sm.schedule_trans_now("idle")

    def on_idle(self):
        self.net.observe("netnow", "connected", lambda: self.sm.schedule_trans_now("active"))

    def on_active(self):
        self.nettime_history = []
        self.tid_history = {}
        self.impl.active(True)
        try:
            # must remove before re-adding
            self.impl.del_peer(broadcast_mac)
        except OSError:
            pass
        # must re-add, otherwise fails silently
        self.impl.add_peer(broadcast_mac)
        self.sm.schedule_trans_now("closed")

    def on_closed(self):
        self.load_peripherals()
        self.sm.recurring_task("netnowc_poll", self.recv, 100 * MILISSECONDS)
        tsk = self.sm.recurring_task("netnowc_nettime", \
                lambda _: self.advance_nettime(nettime_subtype_default), 30 * SECONDS, 10 * SECONDS)
        tsk.advance()
        self.net.observe("netnow", "connlost", lambda: self.sm.schedule_trans_now("inactive"))

    def on_inactive(self):
        self.impl.active(False)
        self.sm.schedule_trans_now("idle")

    # Called e.g. when relevant MQTT topic is pinged
    def opentopair(self):
        self.sm.schedule_trans_now("open")
        
    def on_open(self):
        self.sm.schedule_trans("closed", 5 * MINUTES)
        self.sm.recurring_task("netnowc_poll", self.recv, 100 * MILISSECONDS)
        self.sm.recurring_task("netnowc_nettime", \
                lambda _: self.advance_nettime(nettime_subtype_open), 500 * MILISSECONDS)
        self.net.observe("netnow", "connlost", lambda: self.sm.schedule_trans_now("inactive"))

    def advance_nettime(self, subtype, tid=None):
        nettime = gen_nonce()
        self.nettime_history = [ nettime ] + self.nettime_history
        self.nettime_history = self.nettime_history[:4] # ~2 minutes max, sync with replay_attack

        buf = bytearray([version, type_nettime, subtype]) + self.group + nettime
        if subtype == nettime_subtype_confirm:
            buf += tid
        buf += hmac(self.psk, buf)
        self.impl.send(broadcast_mac, buf, False)

    # Protection against replay attacks
    def is_tid_repeated(self, tid):
        if tid in self.tid_history:
            return True

        self.tid_history[tid] = Shortcronometer()

        # Manage TID cache
        for tid in list(self.tid_history.keys()):
            if self.tid_history[tid].elapsed() > 3 * MINUTES:
                del self.tid_history[tid]
        # TODO memory cap using LRU

        return False

    def register_recv_data(self, observer):
        if observer not in self.data_recv_observers:
            self.data_recv_observers.append(observer)

    def recv(self, _):
        while self.impl.any():
            print("NetNowCentral: recv packet")
            mac, msg = self.impl.recv()
            self.handle_recv_packet(mac, msg)
    
    def handle_recv_packet(self, mac, msg):
        if len(msg) < (2 + hmac_size * 2):
            print("NetNowCentral.handle_recv_packet: invalid len")
            return
        if msg[0] != version:
            print("NetNowCentral.handle_recv_packet: unknown version", version)
            return
        # TODO add group to every packet to allow early filtering at this point?
        if not check_hmac(self.psk, msg):
            print("NetNowCentral.handle_recv_packet: bad hmac")
            return
        pkttype = msg[1]
        nettime = msg[2:hmac_size+2]
        if nettime not in self.nettime_history:
            print("NetNowCentral.handle_recv_packet: bad nettime")
            return
        tid = msg[hmac_size+2:hmac_size*2+2]
        if self.is_tid_repeated(tid):
            print("NetNowCentral.handle_recv_packet: replayed tid")
            return
        payload = msg[hmac_size*2+2:-hmac_size]

        if pkttype == type_data:
            self.handle_data_packet(mac_b2s(mac), tid, payload)
            return

        if pkttype == type_pair:
            self.handle_pair_packet(mac_b2s(mac), tid, payload)
            return

        print("NetNowCentral.handle_recv_packet: unknown type", pkttype)

    def handle_data_packet(self, smac, tid, msg):
        if not self.known_peripheral(smac):
            print("NetNowCentral.handle_data_packet: unpaired peripheral", smac)
            return

        self.sm.onetime_task("netnowc_conf", \
                lambda _: self.advance_nettime(nettime_subtype_confirm, tid), \
                0 * SECONDS)

        for observer in self.data_recv_observers:
            observer.recv_data(smac, msg)

    def handle_pair_packet(self, smac, tid, msg):
        if self.sm.state != 'open':
            return

        if not self.add_peripheral(smac):
            print("NetNowCentral.handle_pair_packet: reject peripheral", smac)
            return

        self.sm.onetime_task("netnowc_conf", \
                lambda _: self.advance_nettime(nettime_subtype_confirm, tid), \
                0 * SECONDS)

    # TODO delegate decision of accepting new peripheral to profile
    # TODO support multiple paired peripherals
    # TODO perhaps even delegate storage of peripheral MACs

    def load_peripherals(self):
        try:
            f = open("pair.txt")
            print("NetNowCentral: forced re-pairing")
            self.nvram.set_str('peripheral', '')
            f.close()
            os.unlink("pair.txt")
        except OSError:
            pass
        self.peripheral = self.nvram.get_str('peripheral') or ""

    def known_peripheral(self, smac):
        return smac == self.peripheral

    def add_peripheral(self, smac):
        self.peripheral = smac
        self.nvram.set_str('peripheral', smac)
        return True
