import network, machine

from epx.loop import Task, SECONDS, MINUTES, StateMachine, reboot, Shortcronometer
from epx import loop

class Net:
    def __init__(self, cfg):
        self.cfg = cfg
        self.impl = None

        sm = self.sm = StateMachine("wifi")
        
        sm.add_state("start", self.on_start)
        sm.add_state("idle", self.on_idle)
        sm.add_state("connecting", self.on_connecting)
        sm.add_state("connected", self.on_connected)
        sm.add_state("connlost", self.on_connlost)

        sm.add_transition("initial", "start")
        sm.add_transition("start", "idle")
        sm.add_transition("idle", "connecting")
        sm.add_transition("connecting", "connected")
        sm.add_transition("connected", "connlost")
        sm.add_transition("connecting", "connlost")
        sm.add_transition("connlost", "idle")

        if 'ssid' in self.cfg.data:
            if 'password' not in self.cfg.data:
                self.cfg.data['password'] = None
            # Delay startup of WiFi to after the watchdog is active (10s)
            startup_time = hasattr(machine, 'TEST_ENV') and 1 or 12
            self.sm.schedule_trans("start", startup_time * SECONDS)

    def observe(self, name, state, cb):
        self.sm.observe(name, state, cb)

    def on_start(self):
        self.impl = network.WLAN(network.STA_IF)
        self.impl.active(False)
        self.sm.schedule_trans("idle", 1 * SECONDS)
        self.last_connection = Shortcronometer()

    def on_idle(self):
        self.impl.active(False)
        if self.last_connection.elapsed() > 10 * MINUTES:
            print("WiFi repeated failures, trying device reboot")
            loop.reboot()
        self.sm.schedule_trans("connecting", 1 * SECONDS)

    def on_connecting(self):
        self.impl.active(True)
        self.impl.connect(self.cfg.data['ssid'], self.cfg.data['password'])
        self.sm.schedule_trans("connlost", 60 * SECONDS)
        self.sm.recurring_task("wifi_poll1", self.connecting_poll, 1 * SECONDS)

    def connecting_poll(self, _):
        ws = self.impl.status()

        if ws == network.STAT_CONNECTING:
            pass
        elif ws == network.STAT_GOT_IP:
            self.sm.schedule_trans_now("connected")
        elif ws == network.STAT_WRONG_PASSWORD:
            print("WiFi wrong password")
            self.sm.schedule_trans_now("connlost")
        elif ws == network.STAT_NO_AP_FOUND:
            print("WiFi no AP found")
            self.sm.schedule_trans_now("connlost")
        else:
            # ESP32 and ESP8266 have dissimilar STAT_* values for lesser-common
            # errors, so we need this catch-all
            print("WiFi error", ws)
            self.sm.schedule_trans_now("connlost")

    def on_connected(self):
        print("WiFi connected", self.ifconfig()[1][0])
        self.sm.recurring_task("wifi_poll2", self.connected_poll, 5 * SECONDS)

    def connected_poll(self, _):
        ws = self.impl.status()

        if ws == network.STAT_GOT_IP:
            pass
        else:
            print("WiFi error", ws)
            self.last_connection = Shortcronometer()
            self.sm.schedule_trans_now("connlost")

    def on_connlost(self):
        print("WiFi connection lost")
        self.impl.active(False)
        self.sm.schedule_trans("idle", 30 * SECONDS, fudge=30 * SECONDS)

    def ifconfig(self):
        return self.sm.state, (self.impl and self.impl.ifconfig() or None)
