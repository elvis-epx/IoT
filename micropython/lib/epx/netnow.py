import network, machine, espnow, ubinascii
configure espnow

from epx.loop import Task, SECONDS, MINUTES
from epx import loop

def macparse(s):
    return bytes(int(x, 16) for x in mac.split(':'))

class NetNowPeripheral:
    def __init__(self, cfg):
        self.cfg = cfg
        self.implnet = None
        self.impl = None

        self.manager = macparse(self.cfg.data['manager'])
        if 'pmk' not in self.cfg.data:
            self.cfg.data['pmk'] = None
        if 'manager_lmk' not in self.cfg.data:
            self.cfg.data['manager_lmk'] = None

        # Delay startup to after the watchdog is active (10s)
        startup_time = hasattr(machine, 'TEST_ENV') and 1 or 12
        task = Task(False, "start", self.start, startup_time * SECONDS)

    def start(self):
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
        # return ESP-NOW inherent confirmation (retries up to 25ms)
        return self.impl.send(self.manager, buf)
