import machine
import os
import os.path


singleton = None

def test_mock():
    f = "wifi.sim"
    if not os.path.exists(f):
        return False
    print("Got wifi.sim")
    cmd = open(f).read().strip()
    os.remove(f)
    if singleton._status > STAT_OFF:
        singleton._status = globals()["STAT_" + cmd]
    return True


STA_IF = 1

STAT_OFF = -1
STAT_IDLE = 0
STAT_GOT_IP = 1
ETH_GOT_IP = 1
STAT_CONNECTING = 2
STAT_WRONG_PASSWORD = 3
STAT_NO_AP_FOUND = 4
STAT_UNDEF_ERROR = 5

PHY_JL1101=1
PHY_GENERIC=2

class WLAN:
    def __init__(self, kind):
        global singleton
        singleton = self
        self._status = STAT_OFF
        self._channel = 1
        machine._wifi = self # for simulation of socket failures in mqttsimple
        pass

    def active(self, new_state):
        if new_state:
            self._status = STAT_IDLE
        else:
            self._status = STAT_OFF
        pass

    def connect(self, ssid, password):
        if self._status > STAT_OFF:
            self._status = STAT_CONNECTING

    def status(self):
        return self._status

    def ifconfig(self):
        if self._status == STAT_GOT_IP:
            return ("1.2.3.4", "1.2.3.5", "1.2.3.6", "1.2.3.7")
        else:
            return ("0.0.0.0", "0.0.0.0", "0.0.0.0", "0.0.0.0")

    def config(self, *args, **kwargs):
        if 'mac' in args:
            return b'\x01\x02\x03\x04\x05\x06'
        if 'channel' in args:
            return self._channel
        if 'channel' in kwargs:
            channel = kwargs['channel']
            if channel < 1 or channel > 13:
                raise Exception("Bad WiFi channel")
            self._channel = channel

class LAN:
    def __init__(self, **phyparams):
        global singleton
        singleton = self
        self._status = STAT_OFF
        machine._wifi = self # for simulation of socket failures in mqttsimple
        pass

    def active(self, new_state):
        if new_state:
            self._status = STAT_IDLE
        else:
            self._status = STAT_OFF
        pass

    def connect(self, ssid, password):
        if self._status > STAT_OFF:
            self._status = STAT_CONNECTING

    def status(self):
        return self._status

    def ifconfig(self):
        if self._status == ETH_GOT_IP:
            return ("1.2.3.4", "1.2.3.5", "1.2.3.6", "1.2.3.7")
        else:
            return ("0.0.0.0", "0.0.0.0", "0.0.0.0", "0.0.0.0")
