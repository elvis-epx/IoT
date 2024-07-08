import network, machine, espnow, errno, os
from hashlib import sha256

from epx.loop import MINUTES, SECONDS, MILISSECONDS, StateMachine, Shortcronometer
from epx import loop

broadcast_mac = b'\xff\xff\xff\xff\xff\xff'
version = const(0x02)

type_data = const(0x01)

type_timestamp = const(0x02)
timestamp_subtype_default = const(0x00)
timestamp_subtype_confirm = const(0x01)

type_ping = const(0x03)

def mac_s2b(s):
    return bytes(int(x, 16) for x in s.split(':'))

def mac_b2s(mac):
    return ':'.join([f"{b:02X}" for b in mac])

def b2s(data):
    return ':'.join([f"{b:02X}" for b in data])

group_size = const(8)
hmac_size = const(12)
tid_size = const(12)
timestamp_size = const(12)

def decode_timestamp(b):
    return int.from_bytes(b, 'big')

def gen_initial_timestamp():
    b = bytearray(os.urandom(timestamp_size))
    b[0] &= 0x80
    return decode_timestamp(b)

def encode_timestamp(n):
    return n.to_bytes(timestamp_size, 'big')

def gen_tid():
    return os.urandom(tid_size)

hash_size = 32

def hash(data):
    h = sha256()
    h.update(data)
    return h.digest()

def group_hash(group):
    return hash(group)[0:group_size]

def prepare_key(key):
    if len(key) <= hash_size:
        return key + bytearray([ 0x00 for _ in range(len(key), hash_size)])
    return hash(key)

def xor(a, b):
    if len(a) > len(b):
        a, b = b, a
    return bytes(x ^ y for x, y in zip(a, b)) + b[len(a):]

ipad = bytearray( 0x36 for _ in range(0, hash_size))
opad = bytearray( 0x5c for _ in range(0, hash_size))

def hmac(key, data):
    return hash(xor(key, opad) + hash(xor(key, ipad) + data))[:hmac_size]

def check_hmac(key, data):
    return hmac(key, data[:-hmac_size]) == data[-hmac_size:]


class NetNowPeripheral:
    def __init__(self, cfg, nvram, watchdog):
        self.cfg = cfg
        self.nvram = nvram
        self.implnet = None
        self.impl = None
        self.current_timestamp = None
        self.last_ping = None
        self.tids = {}

        self.group = group_hash(self.cfg.data['espnowgroup'].encode())
        self.psk = prepare_key(self.cfg.data['espnowpsk'].encode())

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

    def is_ready(self):
        return self.sm.state == 'paired' and self.current_timestamp is not None

    def on_start(self):
        self.implnet = network.WLAN(network.STA_IF)
        self.implnet.active(False)
        self.implnet.active(True)

        self.impl = espnow.ESPNow()
        self.impl.active(True)

        try:
            f = open("pair.txt")
            print("netnow: forced re-pairing")
            self.nvram.set_str('manager', '')
            f.close()
            os.unlink("pair.txt")
        except OSError:
            pass

        # clean rx buffer
        while self.impl.any():
            self.impl.recv()

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

    def on_paired(self):
        manager = self.nvram.get_str('manager') or ""
        self.manager = mac_s2b(manager)
        self.channel = self.nvram.get_int('channel')
        self.impl.add_peer(self.manager)
        self.implnet.config(channel=self.channel)
        print("netnow: paired w/", manager, "channel", self.channel)
        self.common_tasks()

    def scan_channel(self, _):
        self.channel += 1
        if self.channel > 13:
            self.channel = 1
        self.implnet.config(channel=self.channel)
        print("netnow: now scanning channel",  self.channel)

    def recv(self, _):
        while self.impl.any():
            print("netnow: recv packet")
            mac, msg = self.impl.recv()
            self.handle_recv_packet(mac, msg)
    
    def handle_recv_packet(self, mac, msg):
        if len(msg) < 2 + group_size + hmac_size:
            print("netnow.handle_recv_packet: invalid len")
            return

        if msg[0] != version:
            print("netnow.handle_recv_packet: unknown version", version)
            return

        pkttype = msg[1]
        group = msg[2:2+group_size]

        if group != self.group:
            print("netnow.handle_recv_packet: not my group", group)
            return

        print("netnow.handle_recv_packet: hmac", b2s(msg[-hmac_size:]))
        if not check_hmac(self.psk, msg):
            print("netnow.handle_recv_packet: bad hmac")
            return

        msg = msg[2+group_size:-hmac_size]

        if pkttype == type_timestamp:
            self.handle_timestamp(mac_b2s(mac), msg)
            return

        print("netnow.handle_recv_packet: unknown type", pkttype)

    def handle_timestamp(self, mac, msg):
        print("netnow: timestamp")

        if len(msg) < (1 + timestamp_size):
            print("... invalid len")
            return

        subtype = msg[0]
        timestamp = decode_timestamp(msg[1:1+timestamp_size])

        if not self.trust_timestamp(subtype, timestamp):
            return

        if self.sm.state == 'unpaired':
            # Adopt this central host as my manager
            self.manager = mac_s2b(mac)
            self.nvram.set_str('manager', mac_b2s(self.manager))
            self.nvram.set_int('channel', self.channel)
            self.sm.schedule_trans_now('paired')
            return

        if subtype == timestamp_subtype_confirm:
            if len(msg) != (1 + timestamp_size + tid_size):
                print("... invalid confirm len")
                return
            tid = msg[1+tid_size:]
            self.tid_confirm(tid, timestamp)
            return

    def trust_timestamp(self, subtype, timestamp):
        if self.current_timestamp is None:
            # timestamp unknown (device just started up)

            if self.sm.state == 'unpaired':
                # trust right away
                print("...timestamp trusted bc unpaired")
                self.current_timestamp = timestamp
                self.last_ping = None
                return True

            if subtype == timestamp_subtype_default:
                # send ping to confirm it is legit
                print("...timestamp untrusted")
                self.send_ping(timestamp)
                # (TID confirmation callback will fill current_timestamp)
                return False

            # ping confirm comes through here
            return True

        # timestamp already known
        diff = timestamp - self.current_timestamp
        if diff > 0 and diff < 100:
            # Legit timestamp advancement
            self.current_timestamp = timestamp
            self.last_ping = None
            return True

        if diff == 0:
            # replay attack
            print("...timestamp replayed")
            return False

        # replay attack, or central may have rebooted
        # keep current timestamp and ping to confirm new one

        if subtype == timestamp_subtype_default:
            print("...timestamp jump")
            self.send_ping(timestamp)
            # (TID confirmation callback will fill current_timestamp)
            return False

        # ping confirm comes through here
        return True

    def tid_cleanup(self):
        for tid in list(self.tids.keys()):
            if self.tids[tid]["crono"].elapsed() > self.tids[tid]["timeout"]:
                del self.tids[tid]

    def tid_confirm(self, tid, timestamp):
        if tid in self.tids:
            print("confirm", b2s(tid))
            self.tids[tid]["cb"](timestamp)
            del self.tids[tid]
        self.tid_cleanup()

    def on_tid_confirm(self, timeout, tid, cb):
        self.tids[tid] = {"crono": Shortcronometer(), "timeout": timeout, "cb": cb}
        self.tid_cleanup()

    def send_ping(self, putative_timestamp):
        if (self.last_ping is not None) and self.last_ping.elapsed() < 10 * SECONDS:
            print("ping still in flight, not sending another")
            return
        self.last_ping = Shortcronometer()

        tid = gen_tid()
        buf = bytearray([version, type_ping])
        buf += self.group
        buf += encode_timestamp(putative_timestamp)
        buf += tid
        buf += hmac(self.psk, buf)

        self.impl.send(self.manager, buf, False)
        print("sent ping tid", b2s(tid), "for timestamp", putative_timestamp % 100000)

        def confirm(timestamp):
            print("timestamp confirmed:", timestamp % 100000)
            self.current_timestamp = timestamp
            self.last_ping = None
        self.on_tid_confirm(5 * SECONDS, tid, confirm)

        return True

    # TODO refactor to use on_tid_confirm

    def send_data_unconfirmed(self, payload):
        if not self.is_ready():
            return False

        tid = gen_tid()
        buf = bytearray([version, type_data])
        buf += self.group
        buf += encode_timestamp(self.current_timestamp)
        buf += tid
        buf += payload
        buf += hmac(self.psk, buf)

        self.impl.send(self.manager, buf, False)
        print("sent data tid", b2s(tid))
        return True

    def send_data_confirmed(self, payload):
        if not self.is_ready():
            return False

        tid = gen_tid()
        buf = bytearray([version, type_data])
        buf += self.group
        buf += encode_timestamp(self.current_timestamp)
        buf += tid
        buf += payload
        buf += hmac(self.psk, buf)

        try:
            # return ESP-NOW inherent confirmation (retries up to 25ms)
            res = self.impl.send(self.manager, buf, True)
            print("sent data tid", b2s(tid))
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
        self.psk = prepare_key(self.cfg.data['espnowpsk'].encode())

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

        self.timestamp = gen_initial_timestamp()

        self.sm.schedule_trans_now("idle")

    def on_idle(self):
        self.net.observe("netnow", "connected", lambda: self.sm.schedule_trans_now("active"))

    def on_active(self):
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
        self.sm.recurring_task("netnowc_poll", self.recv, 100 * MILISSECONDS)
        tsk = self.sm.recurring_task("netnowc_timestamp", \
                lambda _: self.advance_timestamp(timestamp_subtype_default), 30 * SECONDS, 10 * SECONDS)
        tsk.advance()
        self.net.observe("netnow", "connlost", lambda: self.sm.schedule_trans_now("inactive"))

    def on_inactive(self):
        self.impl.active(False)
        self.sm.schedule_trans_now("idle")

    # Called e.g. when relevant MQTT topic is pinged
    def opentopair(self):
        self.sm.schedule_trans_now("open")

    def on_open(self):
        self.sm.recurring_task("netnowc_poll", self.recv, 100 * MILISSECONDS)
        self.sm.recurring_task("netnowc_timestamp", \
                lambda _: self.advance_timestamp(timestamp_subtype_default), 500 * MILISSECONDS)
        self.net.observe("netnow", "connlost", lambda: self.sm.schedule_trans_now("inactive"))

        self.sm.schedule_trans("closed", 5 * MINUTES)

    def advance_timestamp(self, subtype, tid=None):
        self.timestamp += 1
        print("Timestamp", self.timestamp % 100000)

        buf = bytearray([version, type_timestamp])
        buf += self.group
        buf += bytearray([subtype])
        buf += encode_timestamp(self.timestamp)
        if subtype == timestamp_subtype_confirm:
            buf += tid
            print("   and confirming tid", b2s(tid))
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
        if len(msg) < (2 + group_size + timestamp_size + tid_size + hmac_size):
            print("NetNowCentral.handle_recv_packet: too short")
            return

        if msg[0] != version:
            print("NetNowCentral.handle_recv_packet: unknown version", version)
            return

        pkttype = msg[1]
        group = msg[2:2+group_size]

        if group != self.group:
            print("NetNowCentral.handle_recv_packet: not my group")
            return

        print("NetNowCentral.handle_recv_packet: hmac", b2s(msg[-hmac_size:]))
        if not check_hmac(self.psk, msg):
            print("NetNowCentral.handle_recv_packet: bad hmac")
            return

        msg = msg[2+group_size:-hmac_size]
        timestamp = decode_timestamp(msg[0:timestamp_size])

        if timestamp > self.timestamp:
            print("NetNowCentral.handle_recv_packet: future timestamp")
            return
        if timestamp < (self.timestamp - 4):
            print("NetNowCentral.handle_recv_packet: past timestamp")
            return
        
        msg = msg[timestamp_size:]
        tid = msg[0:tid_size]

        if self.is_tid_repeated(tid):
            print("NetNowCentral.handle_recv_packet: replayed tid")
            return

        msg = msg[tid_size:]

        if pkttype == type_data:
            self.handle_data_packet(mac_b2s(mac), tid, msg)
            return

        if pkttype == type_ping:
            self.handle_ping_packet(mac_b2s(mac), tid)
            return

        print("NetNowCentral.handle_recv_packet: unknown type", pkttype)

    def handle_data_packet(self, smac, tid, msg):
        print("NetNowCentral.handle_data_packet")
        self.sm.onetime_task("netnowc_conf", \
                lambda _: self.advance_timestamp(timestamp_subtype_confirm, tid), \
                0 * SECONDS)

        for observer in self.data_recv_observers:
            observer.recv_data(smac, msg)

    def handle_ping_packet(self, smac, tid):
        print("NetNowCentral.handle_ping_packet")
        self.sm.onetime_task("netnowc_conf", \
                lambda _: self.advance_timestamp(timestamp_subtype_confirm, tid), \
                0 * SECONDS)
