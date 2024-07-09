import network, machine, espnow, errno, os

from epx.loop import MINUTES, SECONDS, MILISSECONDS, StateMachine, Shortcronometer, Longcronometer
from epx import loop

from epx.netnow import *

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
        sm.add_state("inactive", self.on_inactive)

        sm.add_transition("initial", "idle")
        sm.add_transition("idle", "active")
        sm.add_transition("active", "inactive")
        sm.add_transition("inactive", "idle")

        self.timestamp_base = gen_initial_timestamp()
        self.timestamp_delta = Longcronometer()
        self.timestamp_delta2 = 0

        self.sm.schedule_trans_now("idle")

    def on_idle(self):
        self.net.observe("netnow", "connected", lambda: self.sm.schedule_trans_now("active"))

    def on_active(self):
        self.tid_history = {}
        self.last_pairreq = None
        self.impl.active(True)
        try:
            # must remove before re-adding
            self.impl.del_peer(broadcast_mac)
        except OSError:
            pass
        # must re-add, otherwise fails silently
        self.impl.add_peer(broadcast_mac)

        self.impl.irq(self.recv)
        self.timestamp_task = self.sm.recurring_task("netnowc_timestamp", \
                lambda _: self.broadcast_timestamp(timestamp_subtype_default), \
                30 * SECONDS, 10 * SECONDS)
        self.timestamp_task.advance()
        self.net.observe("netnow", "connlost", lambda: self.sm.schedule_trans_now("inactive"))

    def on_inactive(self):
        self.impl.active(False)
        self.sm.schedule_trans_now("idle")

    def current_timestamp(self):
        return self.timestamp_base + int(self.timestamp_delta.elapsed()) + self.timestamp_delta2

    def broadcast_timestamp(self, subtype, tid=None):
        # makes sure consecutive broadcasts will send different timestamps
        self.timestamp_delta2 += 1

        current_timestamp = self.current_timestamp()
        print("Timestamp", current_timestamp % 1000000)

        buf = bytearray([version, type_timestamp])
        buf += self.group
        buf += bytearray([subtype])
        buf += encode_timestamp(current_timestamp)
        if subtype == timestamp_subtype_confirm:
            buf += tid
            print("   and confirming tid", b2s(tid))
        buf += hmac(self.psk, buf)

        self.impl.send(broadcast_mac, buf, False)

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
            mac, msg = self.impl.recv()
            self.schedule_handle_recv_packet(mac, msg)

    def schedule_handle_recv_packet(self, mac, msg):
        self.sm.onetime_task("recv", lambda _: self.handle_recv_packet(mac, msg), 0)
    
    def handle_recv_packet(self, mac, msg):
        print("netnow.handle_recv_packet")
        if (self.last_pairreq is not None) and self.last_pairreq.elapsed() > 30 * SECONDS:
            self.last_pairreq = None

        if len(msg) < (2 + group_size + timestamp_size + tid_size + hmac_size):
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

        if not check_hmac(self.psk, msg):
            print("...bad hmac")
            return

        print("...from", mac_b2s(mac), "pkttype", pkttype)

        if pkttype == type_pairreq:
            self.handle_pairreq_packet()
            return

        msg = msg[2+group_size:-hmac_size]
        timestamp = decode_timestamp(msg[0:timestamp_size])

        current_timestamp = self.current_timestamp()
        if timestamp > current_timestamp:
            print("...future timestamp")
            return
        if timestamp < (current_timestamp - 2 * MINUTES):
            print("...past timestamp")
            return
        
        msg = msg[timestamp_size:]
        tid = msg[0:tid_size]

        if self.is_tid_repeated(tid):
            print("...replayed tid")
            return

        msg = msg[tid_size:]

        if pkttype == type_data:
            self.handle_data_packet(mac_b2s(mac), tid, msg)
            return

        if pkttype == type_ping:
            self.handle_ping_packet(mac_b2s(mac), tid)
            return

        print("...unknown type", pkttype)

    def handle_data_packet(self, smac, tid, msg):
        print("netnow.handle_data_packet")
        self.sm.onetime_task("netnowc_conf", \
                lambda _: self.broadcast_timestamp(timestamp_subtype_confirm, tid), \
                0 * SECONDS)

        for observer in self.data_recv_observers:
            observer.recv_data(smac, msg)

    def handle_ping_packet(self, smac, tid):
        print("netnow.handle_ping_packet")
        self.sm.onetime_task("netnowc_conf", \
                lambda _: self.broadcast_timestamp(timestamp_subtype_confirm, tid), \
                0 * SECONDS)

    def handle_pairreq_packet(self):
        print("netnow.handle_pairreq_packet")
        if self.last_pairreq is not None:
            print("...pairreq still recent, not sending another")
            return
        self.last_pairreq = Shortcronometer() # cleaned by handle_recv_packet

        self.timestamp_task.advance()
