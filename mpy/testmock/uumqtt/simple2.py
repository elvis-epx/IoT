import machine
import network
import os
import os.path
import random
from epx import loop
import socket

singleton = None

def test_mock():
    f = machine.TEST_FOLDER + "mqttblock.sim"
    if os.path.exists(f):
        print("Got mqttblock.sim")
        os.remove(f)
        singleton.mqttblock = True
        return True

    f = machine.TEST_FOLDER + "mqttfail.sim"
    if os.path.exists(f):
        print("Got mqttfail.sim")
        mode = open(f).read().strip()
        os.remove(f)
        singleton.mqttfail[mode] = 1
        return True

    if singleton is None or singleton.pipe_w is None:
        return False

    if 'checkmsg' in singleton.mqttfail:
        singleton.pipe_w.send(b'c')
        return True

    f = machine.TEST_FOLDER + "mqttsub.sim"
    if os.path.exists(f):
        singleton.pipe_w.send(b'i')
        return True

    return False


class MQTTException(Exception):
    pass


class MQTTClient:
    def __init__(self, device_id, broker):
        global singleton
        singleton = self
        self.subscribed = {}
        self.sub_cb = lambda t, m, r, d: None
        self.state = 0
        self.mqttblock = False
        self.mqttfail = {}
        self.pipe_r = self.pipe_w = None

    def set_callback(self, sub_cb):
        self.sub_cb = sub_cb

    def connect(self):
        if 'connect_permanent' in self.mqttfail:
            raise MQTTException("server not found")
        if 'connect' in self.mqttfail:
            del self.mqttfail['connect']
            raise MQTTException("server not found")
        self.simulate_socket_failure()
        self.simulate_socket_block()
        self.pipe_r, self.pipe_w = socket.socketpair()
        self.sock = self.pipe_r
        self.state = 1
        return False # returns persistent connection

    def disconnect(self):
        self.state = 0
        if self.pipe_r:
            self.pipe_r.close()
            self.pipe_r = None
        if self.pipe_w:
            self.pipe_w.close()
            self.pipe_w = None
        if getattr(self, 'sock', None):
            self.sock.close()
        if random.random() > 0.5:
            raise MQTTException("simulate umqtt.simple failure (not simple2)")

    def subscribe(self, topic):
        self.simulate_socket_failure()
        self.simulate_socket_block()
        self.subscribed[topic] = 1

    def check_msg(self):
        self.pipe_r.recv(1)
        if 'checkmsg' in self.mqttfail:
            del self.mqttfail['checkmsg']
            raise MQTTException("server disconn")
        self.simulate_socket_failure()
        f = machine.TEST_FOLDER + "mqttsub.sim"
        if not os.path.exists(f):
            return False
        print("Got mqttsub.sim")
        rows = open(f, 'rb').readlines()
        topic = rows[0].strip()
        msg = rows[1].strip()
        retained = len(rows) > 2 and rows[2].strip() == b'1'
        dup = len(rows) > 3 and rows[3].strip() == b'1'
        os.remove(f)
        self.sub_cb(topic, msg, retained, dup)
        return True

    def publish(self, topic, msg, retain):
        if 'publish' in self.mqttfail:
            del self.mqttfail['publish']
            raise MQTTException("server disconn")
        self.simulate_socket_failure()
        self.simulate_socket_block()
        f = machine.TEST_FOLDER + "mqttpub.sim"
        open(f, 'ab').write(topic + b' ' + msg + b' ' + (retain and b'retain' or b'noretain') + b'\n')
        if self.mqttblock:
            print("Simulate MQTT socket block")
            loop.sleep(5000)
            self.mqttblock = False

    def ping(self):
        if 'ping' in self.mqttfail:
            del self.mqttfail['ping']
            raise MQTTException("server disconn")
        self.simulate_socket_failure()
        self.simulate_socket_block()
        f = machine.TEST_FOLDER + "mqttping.sim"
        open(f, 'a').write('ping\n')

    def simulate_socket_block(self):
        if self.mqttblock:
            print("Simulate MQTT socket block")
            loop.sleep(5000)
            self.mqttblock = False

    def simulate_socket_failure(self):
        if not machine._wifi:
            raise MQTTException("no wifi")
        if machine._wifi.status() != network.STAT_GOT_IP:
            raise MQTTException("wifi not connected")
