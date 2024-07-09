import network, machine, espnow, errno, os

from epx.loop import MINUTES, SECONDS, MILISSECONDS, StateMachine, Shortcronometer
from epx import loop

from epx.netnow import *

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
        self.impl.irq(self.recv)

    def on_unpaired(self):
        self.channel = 0
        self.impl.add_peer(broadcast_mac)
        tsk = self.sm.recurring_task("netnowp_scan", self.scan_channel, 5 * SECONDS)
        tsk.advance()
        self.sm.recurring_task("netnowp_pairreq", self.send_pairreq, 1 * SECONDS)
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
            mac, msg = self.impl.recv()
            self.schedule_handle_recv_packet(mac, msg)

    def schedule_handle_recv_packet(self, mac, msg):
        self.sm.onetime_task("recv", lambda _: self.handle_recv_packet(mac, msg), 0)
    
    def handle_recv_packet(self, mac, msg):
        print("netnow.handle_recv_packet")

        if len(msg) < 2 + group_size + hmac_size:
            print("...invalid len")
            return

        if msg[0] != version:
            print("...unknown version", version)
            return

        pkttype = msg[1]
        group = msg[2:2+group_size]

        if group != self.group:
            print("...not my group", group)
            return

        print("...hmac", b2s(msg[-hmac_size:]))
        if not check_hmac(self.psk, msg):
            print("...bad hmac")
            return

        msg = msg[2+group_size:-hmac_size]

        if pkttype == type_timestamp:
            self.handle_timestamp(mac_b2s(mac), msg)
            return

        print("...unknown type", pkttype)

    def handle_timestamp(self, mac, msg):
        print("netnow: handle_timestamp")

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
        if diff > 0 and diff < 5 * MINUTES:
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

    def send_pairreq(self, _):
        buf = bytearray([version, type_pairreq])
        buf += self.group
        buf += encode_timestamp(0)
        buf += bytearray([0 for _ in range(0, tid_size)])
        buf += hmac(self.psk, buf)

        self.impl.send(broadcast_mac, buf, False)
        print("sent pair req")

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
        print("sent ping tid", b2s(tid), "for timestamp", putative_timestamp % 1000000)

        def confirm(timestamp):
            print("timestamp confirmed:", timestamp % 1000000)
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
