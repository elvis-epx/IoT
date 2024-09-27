import network, machine, espnow, errno, os

from epx.loop import MINUTES, SECONDS, MILISSECONDS, StateMachine, Shortcronometer, POLLIN

from epx.netnow import *

class NetNowPeripheral:
    def __init__(self, cfg, nvram, watchdog):
        self.cfg = cfg
        self.nvram = nvram
        self.implnet = None
        self.impl = None
        self.timestamp_recv = 0
        self.timestamp_delay = 0
        self.timestamp_age = Shortcronometer()
        self.last_ping = None
        self.tids = {}
        self.ttid_history = {}
        self.data_recv_observers = []

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
        return self.sm.state == 'paired' and self.timestamp_recv != 0

    def register_recv_data(self, observer):
        if observer not in self.data_recv_observers:
            self.data_recv_observers.append(observer)

    def clean_rx_buffer(self):
        while self.impl.any():
            self.impl.recv()

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

        self.clean_rx_buffer()

        manager = self.nvram.get_str('manager') or ""
        if bool(manager):
            self.sm.schedule_trans_now("paired")
        else:
            self.sm.schedule_trans_now("unpaired")

    def recv_tasks(self):
        self.sm.poll_object("espnow", self.impl, POLLIN, self.recv)

    def on_unpaired(self):
        self.channel = 0
        self.impl.add_peer(broadcast_mac)
        self.recv_tasks()
        tsk = self.sm.recurring_task("netnowp_scan", self.scan_channel, 5 * SECONDS)
        tsk.advance()
        self.sm.recurring_task("netnowp_pairreq", self.send_pairreq, 1 * SECONDS)
        self.wakeup_task = None

    def on_paired(self):
        manager = self.nvram.get_str('manager') or ""
        self.manager = mac_s2b(manager)
        self.channel = self.nvram.get_int('channel')
        self.impl.add_peer(self.manager)
        self.implnet.config(channel=self.channel)
        self.recv_tasks()
        print("netnow: paired w/", manager, "channel", self.channel)
        self.wakeup_task = self.sm.recurring_task("netnowp_wakeup", self.send_wakeup, 5 * SECONDS)
        self.wakeup_task.advance()

    def scan_channel(self, _):
        # increment channel and keep it in the range 1..13
        self.channel = self.channel % 13 + 1
        self.implnet.config(channel=self.channel)
        print("netnow: now scanning channel",  self.channel)

    def recv(self, _):
        while self.impl.any():
            mac, msg = self.impl.recv()
            self.schedule_handle_recv_packet(mac, msg)

    def schedule_handle_recv_packet(self, mac, msg):
        my_timestamp = self.timestamp_current()
        self.sm.onetime_task("recv", lambda _: self.handle_recv_packet(mac, msg, my_timestamp), 0)
    
    def handle_recv_packet(self, mac, msg, my_timestamp):
        print("netnow.handle_recv_packet")

        if not check_hmac(self.psk, msg):
            print("...bad hmac")
            return

        msg = msg[:-hmac_size]
        msg = decrypt(self.psk, msg)

        if msg is None:
            print("...cannot decrypt")
            return

        if len(msg) < 2 + group_size:
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

        msg = msg[2+group_size:]

        if pkttype != type_timestamp:
            print("...unknown type", pkttype)
            return

        mac = mac_b2s(mac)

        if len(msg) < (1 + tid_size + timestamp_size):
            print("... invalid len")
            return

        subtype, ttid, msg = msg[0], msg[1:1 + tid_size], msg[1 + tid_size:]
        print("... ttid", b2s(ttid))
        timestamp = decode_timestamp(msg[0:timestamp_size])
        msg = msg[timestamp_size:]

        if not self.trust_timestamp(subtype, ttid, timestamp, my_timestamp):
            return

        if self.sm.state == 'unpaired':
            # Adopt this central host as my manager
            self.manager = mac_s2b(mac)
            self.nvram.set_str('manager', mac_b2s(self.manager))
            self.nvram.set_int('channel', self.channel)
            self.sm.schedule_trans_now('paired')
            return

        if subtype == timestamp_subtype_confirm:
            if len(msg) != tid_size:
                print("... invalid confirm len")
                return
            tid = msg
            print("... confirmed", b2s(tid))
            self.tid_confirm(tid, timestamp, my_timestamp)

        elif subtype == timestamp_subtype_backdata:
            for observer in self.data_recv_observers:
                observer.recv_data(ttid, msg)

    def trust_timestamp(self, subtype, ttid, timestamp, my_timestamp):
        if self.is_ttid_repeated(ttid):
            print("...replayed ttid")
            return False

        if self.timestamp_recv == 0:
            # network time unknown (device just started up)

            if self.sm.state == 'unpaired':
                print("...timestamp trusted bc unpaired", timestamp % 1000000)
                processing_delay = self.timestamp_current() - my_timestamp
                self.rebase_timestamp(timestamp, processing_delay)
                return True

            if subtype != timestamp_subtype_confirm:
                print("...timestamp untrusted bc waiting wakeup", timestamp % 1000000)
                return False

            # wakeup confirm comes through here
            return True

        # timestamp already known
        diff = timestamp - self.timestamp_recv
        diff2 = timestamp - my_timestamp
        processing_delay = self.timestamp_current() - my_timestamp

        if diff == 0:
            # replay attack
            print("...timestamp replayed")
            return False

        if (diff > 0 and diff < 2 * MINUTES) and abs(diff2) < 1 * SECONDS:
            # Legit timestamp advancement
            print("...new timestamp", timestamp % 1000000, "diff", diff, diff2, processing_delay)
            self.rebase_timestamp(timestamp, processing_delay)
            return True

        # replay attack, or central may have rebooted
        # keep current timestamp and ping to confirm new one

        if subtype != timestamp_subtype_confirm:
            print("...timestamp gap", diff, diff2)
            self.send_ping(timestamp)
            # (TID confirmation callback will fill timestamp_recv)
            return False

        # ping confirm comes through here
        return True

    def is_ttid_repeated(self, ttid):
        if ttid in self.ttid_history:
            return True

        self.ttid_history[ttid] = Shortcronometer()

        # Manage Timestamp TID cache
        for ttid in list(self.ttid_history.keys()):
            if self.ttid_history[ttid].elapsed() > 2 * SECONDS:
                # print("retired ttid", b2s(ttid))
                del self.ttid_history[ttid]
        # TODO memory cap using LRU

        return False

    def tid_cleanup(self):
        for tid in list(self.tids.keys()):
            if self.tids[tid]["crono"].elapsed() > self.tids[tid]["timeout"]:
                print("timeout tid", b2s(tid))
                del self.tids[tid]

    def tid_confirm(self, tid, timestamp, my_timestamp):
        if tid in self.tids:
            print("confirm", b2s(tid))
            self.tids[tid]["cb"](timestamp, my_timestamp)
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

        buf = encrypt(self.psk, buf)
        buf += hmac(self.psk, buf)

        self.impl.send(broadcast_mac, buf, False)
        print("sent pair req")

    def send_wakeup(self, _):
        if self.timestamp_recv != 0:
            print("not sending wakeup packet (timestamp already known)")
            self.wakeup_task.cancel()
            self.wakeup_task = None
            return

        tid = gen_tid()
        buf = bytearray([version, type_wakeup])
        buf += self.group
        buf += encode_timestamp(0)
        buf += tid

        buf = encrypt(self.psk, buf)
        buf += hmac(self.psk, buf)

        try:
            self.impl.send(self.manager, buf, True)
        except OSError as err:
            return
        print("sent wakeup tid", b2s(tid))

        def confirm(timestamp, my_timestamp):
            if self.wakeup_task is not None:
                print("timestamp confirmed by wakeup:", timestamp % 1000000)
                processing_delay = self.timestamp_current() - my_timestamp
                self.rebase_timestamp(timestamp, processing_delay)
                self.wakeup_task.cancel()
                self.wakeup_task = None

        self.on_tid_confirm(1 * SECONDS, tid, confirm)

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

        buf = encrypt(self.psk, buf)
        buf += hmac(self.psk, buf)

        self.impl.send(self.manager, buf, False)
        print("sent ping tid", b2s(tid), "for timestamp", putative_timestamp % 1000000)

        def confirm(timestamp, my_timestamp):
            print("timestamp confirmed by ping:", timestamp % 1000000)
            processing_delay = self.timestamp_current() - my_timestamp
            self.rebase_timestamp(timestamp, processing_delay)
        self.on_tid_confirm(5 * SECONDS, tid, confirm)

        return True

    def rebase_timestamp(self, timestamp, processing_delay):
        self.timestamp_recv = timestamp
        self.timestamp_delay = processing_delay
        self.timestamp_age = Shortcronometer()
        self.last_ping = None

    def timestamp_current(self):
        return self.timestamp_recv + self.timestamp_delay + self.timestamp_age.elapsed()

    def send_data(self, payload, confirm_mode):
        if not self.is_ready():
            return False

        tid = gen_tid()
        buf = bytearray([version, type_data])
        buf += self.group
        buf += encode_timestamp(self.timestamp_current())
        buf += tid
        buf += payload

        buf = encrypt(self.psk, buf)
        buf += hmac(self.psk, buf)

        # ESP-NOW inherent confirmation (retries up to 25ms)
        espnow_confirm = (confirm_mode == 1)
        # TODO implement confirm_mode > 1 and add support to use on_tid_confirm

        try:
            res = self.impl.send(self.manager, buf, espnow_confirm) \
                    or not espnow_confirm
        except OSError as err:
            if err.errno == errno.ETIMEDOUT:
                # observed in tests (when espnow_confirm is True)
                return False
            # should not happen
            raise # pragma: no cover

        if res:
            print("sent data tid", b2s(tid))
        return res
