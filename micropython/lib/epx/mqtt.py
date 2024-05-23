import machine
import gc
import os
from uumqtt.simple2 import MQTTClient, MQTTException
import ubinascii

from epx.loop import Task, SECONDS, MILISSECONDS, MINUTES, StateMachine, reboot, Longcronometer
from epx import loop

ota_pub = None
log_pub = None

class MQTT:
    def __init__(self, cfg, net, watchdog):
        self.cfg = cfg
        self.net = net
        self.watchdog = watchdog

        self.publist = []
        self.sublist = {}
        self.name = ""

        sm = self.sm = StateMachine("mqtt")

        sm.add_state("start", self.on_start)
        sm.add_transition("initial", "start")

        sm.add_state("testnet", self.on_testnet)
        sm.add_transition("start", "testnet")

        sm.add_state("connect", self.on_connect)
        sm.add_transition("testnet", "connect")

        sm.add_state("connected", self.on_connected)
        sm.add_transition("connect", "connected")
        sm.add_transition("connect", "connlost")

        sm.add_state("connlost", self.on_connlost)
        sm.add_transition("connected", "connlost")
        sm.add_transition("connlost", "testnet")

        if "mqttbroker" in self.cfg.data and "mqttname" in self.cfg.data:
            self.name = self.cfg.data['mqttname']
            self.sm.schedule_trans("start", 12 * SECONDS)
            global ota_pub, log_pub
            ota_pub = OTAPub(self.net)
            self.pub(ota_pub)
            self.sub(OTASub())
            self.pub(Uptime())
            log_pub = Log()
            self.pub(log_pub)

    def pub(self, pubobj):
        pubobj.adjust_topic(self.name)
        self.publist.append(pubobj)
        return pubobj

    def sub(self, subobj):
        subobj.adjust_topic(self.name)
        self.sublist[subobj.topic] = subobj
        return subobj

    def on_start(self):
        self.disconn_backoff = 500 * MILISSECONDS
        client_id = ubinascii.hexlify(machine.unique_id()).decode('ascii')
        client_id = self.name + client_id
        self.impl = MQTTClient(client_id, self.cfg.data["mqttbroker"])
        self.impl.set_callback(self.received_data)
        self.sm.schedule_trans_now("testnet")

    def on_testnet(self):
        self.net.observe("mqtt", "connected", lambda: self.sm.schedule_trans_now("connect"))

    def on_connect(self):
        if self.connect():
            self.sm.schedule_trans_now("connected")
            return

        self.disconn_backoff *= 2
        if self.disconn_backoff >= 10 * MINUTES:
            loop.reboot("Too much time w/o MQTT connection, rebooting")

        self.sm.schedule_trans_now("connlost")

    def on_connected(self):
        self.disconn_backoff = 500 * MILISSECONDS
        self.ping_task = self.sm.recurring_task("mqtt_ping", self.ping, 20 * SECONDS, fudge=20 * SECONDS)
        self.sm.recurring_task("mqtt_eval", self.eval, 250 * MILISSECONDS)

    def received_data(self, topic, msg, retained, dup):
        if topic in self.sublist:
            self.sublist[topic].recv(topic, msg, retained, dup)
        else:
            print("MQTT recv invalid topic", topic)

    def ping(self, _):
        self.watchdog.may_block()
        try:
            self.impl.ping()
            # print("MQTT ping")
        except (MQTTException, OSError):
           print("MQTT conn fail at ping")
           self.sm.schedule_trans_now("connlost")
        finally:
            self.watchdog.may_block_exit()

    def on_connlost(self):
        self.disconnect()
        self.sm.schedule_trans("testnet", self.disconn_backoff, fudge=self.disconn_backoff)

    def eval(self, _):
        try:
            self.impl.check_msg()
        except (MQTTException, OSError):
            print("MQTT conn fail at check_msg")
            self.sm.schedule_trans_now("connlost")
            return

        for pubobj in self.publist:
            if pubobj.has_changed():
                self.watchdog.may_block() # impl.publish() may block
                try:
                    self.impl.publish(pubobj.topic, pubobj.msg, pubobj.retain)
                    print("MQTT pub %s %s" % (pubobj.topic, pubobj.msg))
                    self.ping_task.restart()
                except (MQTTException, OSError):
                    print("MQTT conn fail at pub")
                    self.sm.schedule_trans_now("connlost")
                finally:
                    self.watchdog.may_block_exit()
                break

    def connect(self):
        result = False
        self.watchdog.may_block() # impl.connect() may block
        try:
            # print("MQTT connecting")
            self.impl.connect()
            for topic in self.sublist:
                self.impl.subscribe(topic)
            # print("MQTT connected")
            result = True
        except (MQTTException, OSError):
            # print("MQTT connection failed")
            pass
        finally:
            self.watchdog.may_block_exit()
        return result

    def disconnect(self):
        try:
            self.impl.disconnect()
        except (OSError, MQTTException):
            pass
        self.impl.sock = None
        # Force underlying closure of socket
        gc.collect()

    def state(self):
        return self.sm.state


class MQTTPub:
    def __init__(self, topic, to, forcepubto, retain):
        self.topic = topic.encode('ascii')
        self.msg = None
        self.changed = False
        self.retain = retain
        if to > 0:
            Task(True, "eval_%s" % topic, self.eval, to).advance()
        if forcepubto > 0:
            Task(True, "force_%s" % topic, self.forcepub, forcepubto)

    def adjust_topic(self, name):
        self.topic = self.topic % name.encode('ascii')

    # May be called manually
    def forcepub(self, _=None):
        self.eval(_, True)

    def eval(self, _, force=False):
        new_msg = self.gen_msg()
        if new_msg is not None:
            new_msg = new_msg.encode('utf-8')
        if force or new_msg != self.msg:
            self.msg = new_msg
            self.changed = self.msg is not None

    def gen_msg(self): # override
        self.msg = None # pragma: no cover

    def has_changed(self):
        changed = self.changed
        self.changed = False
        return changed


class MQTTSub:
    def __init__(self, topic):
        self.topic = topic.encode('ascii')

    def adjust_topic(self, name):
        self.topic = self.topic % name.encode('ascii')

    def recv(self, topic, msg, retained, dup): # override
        pass # pragma: no cover


class OTAPub(MQTTPub):
    def __init__(self, net):
        MQTTPub.__init__(self, "stat/%s/OTA", 10 * SECONDS, 24 * 60 * MINUTES, False)
        self.enabled = False
        self.counter = 0
        self.net = net

    def start_bcast(self):
        self.enabled = True

    def gen_msg(self):
        if not self.enabled:
            return ''
        self.counter += 1
        addr = 'undef'
        mac = self.net.macaddr() or 'undef'
        netstatus, ifconfig = self.net.ifconfig()
        if ifconfig and netstatus == 'connected':
            addr = ifconfig[0]
        return "netstatus %s addr %s mac %s count %d" % (netstatus, addr, mac, self.counter)

class Log(MQTTPub):
    def __init__(self):
        MQTTPub.__init__(self, "stat/%s/Log", 0, 0, False)
        self.logmsg = None

    def gen_msg(self):
        return self.logmsg

    def dump(self, filename):
        try:
            f = open(filename, 'r')
            self.logmsg = f.read()
            f.close()
        except OSError:
            self.logmsg = '(%s not found)' % filename
        self.forcepub()

class OTASub(MQTTSub):
    def __init__(self):
        MQTTSub.__init__(self, "cmnd/%s/OTA")

    def recv(self, topic, msg, retained, dup):
        if msg == b'reboot':
            loop.reboot("Received MQTT reboot cmd")
        elif msg == b'open':
            print("Received MQTT OTA open cmd")
            from epx import ota
            ota.start()
            ota_pub.start_bcast()
        elif msg == b'msg_reboot':
            log_pub.dump('reboot.txt')
        elif msg == b'msg_exception':
            log_pub.dump('exception.txt')
        elif msg == b'test_exception':
            raise Exception("Test exception")
        elif msg == b'msg_rm':
            try:
                os.unlink('reboot.txt')
            except OSError as e:
                pass
            try:
                os.unlink('exception.txt')
            except OSError as e:
                pass


class Uptime(MQTTPub):
    def __init__(self):
        MQTTPub.__init__(self, "stat/%s/Uptime", 60 * SECONDS, 30 * MINUTES, False)
        self.uptime = Longcronometer()

    def gen_msg(self):
        return "%d" % (self.uptime.elapsed() // MINUTES)
