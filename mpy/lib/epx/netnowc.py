import network, machine, espnow, errno, os

from epx.loop import MINUTES, SECONDS, MILISSECONDS, StateMachine, Shortcronometer, POLLIN

from epx.netnow import *

class NetNowCentral:
    def __init__(self, cfg, nvram, watchdog):
        self.cfg = cfg
        self.nvram = nvram
        self.implnet = None
        self.impl = None
        self.data_recv_observers = []

        self.group = group_hash(self.cfg.data['espnowgroup'].encode())
        self.psk = prepare_key(self.cfg.data['espnowpsk'].encode())

        sm = self.sm = StateMachine("netnowc")

        sm.add_state("start", self.on_start)
        sm.add_transition("initial", "start")

        startup_time = hasattr(machine, 'TEST_ENV') and 5 or (watchdog.grace_time() + 1)
        self.sm.schedule_trans("start", startup_time * SECONDS)

    def on_start(self):
        self.timestamp_base = gen_initial_timestamp()
        self.timestamp_delta = Shortcronometer()

        self.implnet = network.WLAN(network.STA_IF)
        self.implnet.active(False)
        self.implnet.active(True)
        self.implnet.config(channel=int(self.cfg.data['espnowchannel']))

        self.impl = espnow.ESPNow()
        self.impl.active(True)

        self.tid_history = {}
        self.pairreq_cts = True
        try:
            # must remove before re-adding
            self.impl.del_peer(broadcast_mac)
        except OSError:
            pass
        # must re-add, otherwise fails silently
        self.impl.add_peer(broadcast_mac)

        self.clean_rx_buffer()
        self.sm.poll_object("espnow", self.impl, POLLIN, self.recv)

        self.timestamp_task = self.sm.recurring_task("netnowc_timestamp", \
                lambda _: self.broadcast_timestamp(timestamp_subtype_default), \
                25 * SECONDS, 10 * SECONDS)
        self.timestamp_task.advance()

    def current_timestamp(self, unique=False):
        self.timestamp_base += int(self.timestamp_delta.elapsed())
        self.timestamp_delta.restart()
        if unique:
            self.timestamp_base += 1
        return self.timestamp_base

    def broadcast_timestamp(self, subtype, tid=None, msg=None):
        # makes sure consecutive broadcasts will send different timestamps
        current_timestamp = self.current_timestamp(True)
        print("Sending timestamp", current_timestamp % 1000000)

        buf = bytearray([version, type_timestamp])
        buf += self.group
        buf += bytearray([subtype])
        buf += gen_tid()
        buf += encode_timestamp(current_timestamp)
        if subtype == timestamp_subtype_confirm:
            buf += tid
            print("...and confirming tid", b2s(tid))
        elif subtype == timestamp_subtype_backdata:
            buf += msg
            print("...plus back data")

        buf = encrypt(self.psk, buf)
        buf += hmac(self.psk, buf)

        self.impl.send(broadcast_mac, buf, False)

    def is_tid_repeated(self, tid):
        if tid in self.tid_history:
            return True

        self.tid_history[tid] = Shortcronometer()

        # Manage TID cache
        for tid in list(self.tid_history.keys()):
            if self.tid_history[tid].elapsed() > 2 * SECONDS:
                # print("retired tid", b2s(tid))
                del self.tid_history[tid]
        # TODO memory cap using LRU

        return False

    def register_recv_data(self, observer):
        if observer not in self.data_recv_observers:
            self.data_recv_observers.append(observer)

    def recv(self, _):
        while self.impl.any():
            mac, msg = self.impl.recv()
            rssi = 1000
            if mac in self.impl.peers_table:
                rssi = self.impl.peers_table[mac][0]
            self.schedule_handle_recv_packet(mac, rssi, msg)

    def schedule_handle_recv_packet(self, mac, rssi, msg):
        my_timestamp = self.current_timestamp()
        self.sm.onetime_task("recv", lambda _: self.handle_recv_packet(mac, rssi, msg, my_timestamp), 0)
    
    def handle_recv_packet(self, mac, rssi, msg, my_timestamp):
        print("netnow.handle_recv_packet RSSI %d" % rssi)

        if not check_hmac(self.psk, msg):
            print("...bad hmac")
            return

        msg = msg[:-hmac_size]
        msg = decrypt(self.psk, msg)

        if msg is None:
            print("...cannot decrypt")
            return

        if len(msg) < (2 + group_size + timestamp_size + tid_size):
            print("...too short")
            return

        if msg[0] != version:
            print("...unknown version", version)
            return

        pkttype = msg[1]
        group = msg[2:2+group_size]

        if group != self.group:
            print("...not my group")
            return

        print("...from", mac_b2s(mac), "pkttype", pkttype)

        msg = msg[2+group_size:]
        timestamp = decode_timestamp(msg[0:timestamp_size])

        msg = msg[timestamp_size:]
        tid = msg[0:tid_size]

        print("...tid",  b2s(tid))

        if pkttype == type_pairreq:
            # TID is ignored
            self.handle_pairreq_packet()
            return

        if self.is_tid_repeated(tid):
            print("...replayed tid")
            return

        if pkttype == type_wakeup:
            # Timestamp is ignored
            self.handle_wakeup_packet(mac_b2s(mac), tid)
            return

        diff = timestamp - my_timestamp

        if diff > 1 * SECONDS:
            print("...future timestamp", diff)
            return
        elif diff < -1 * SECONDS:
            print("...past timestamp", diff)
            return
        print("... timestamp skew", diff)
        
        msg = msg[tid_size:]

        if pkttype == type_data:
            self.handle_data_packet(mac_b2s(mac), rssi, tid, msg)
            return

        if pkttype == type_ping:
            self.handle_ping_packet(mac_b2s(mac), tid)
            return

        print("...unknown type", pkttype)

    def send_confirm(self, tid):
        self.sm.onetime_task("netnowc_conf", \
                lambda _: self.broadcast_timestamp(timestamp_subtype_confirm, tid), \
                0 * SECONDS)
        self.timestamp_task.restart()

    def send_backdata(self, msg):
        self.sm.onetime_task("netnowc_conf", \
                lambda _: self.broadcast_timestamp(timestamp_subtype_backdata, None, msg), \
                0 * SECONDS)
        self.timestamp_task.restart()

    def handle_data_packet(self, smac, rssi, tid, msg):
        print("netnow.handle_data_packet")
        self.send_confirm(tid)
        for observer in self.data_recv_observers:
            observer.recv_data(smac, rssi, msg)

    def handle_ping_packet(self, smac, tid):
        print("netnow.handle_ping_packet")
        self.send_confirm(tid)

    def handle_pairreq_packet(self):
        print("netnow.handle_pairreq_packet")
        if not self.pairreq_cts:
            print("...pairreq still recent, not sending another")
            return
        self.timestamp_task.advance()

        self.pairreq_cts = False
        def restore_cts(_):
            self.pairreq_cts = True
        self.sm.onetime_task("netnowc_pairreqcts", restore_cts, 30 * SECONDS)

    def handle_wakeup_packet(self, smac, tid):
        print("netnow.handle_wakeup_packet")
        self.send_confirm(tid)

    def clean_rx_buffer(self):
        while self.impl.any():
            self.impl.recv()
