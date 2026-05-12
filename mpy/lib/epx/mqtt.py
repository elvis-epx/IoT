import machine
import gc
import os
from uumqtt.simple2 import MQTTClient, MQTTException
import ubinascii

from epx.loop import Task, SECONDS, MILISSECONDS, MINUTES, StateMachine, reboot, Longcronometer, POLLIN
from epx import loop

mqtt_manager = None

class MQTT:
    def __init__(self, cfg, net, watchdog):
        global mqtt_manager
        mqtt_manager = self

        self.cfg = cfg
        self.net = net
        self.watchdog = watchdog

        self.publist = []
        self.pub_pending = []
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

        self.pub(Uptime())
        self.sub(Refresh())

        self.log_pub = Log(self)
        self.pub(self.log_pub)

    def get_connlost_count(self):
        return self.net.get_nvram_int("mqttlost")

    def incr_connlost_count(self):
        self.net.set_nvram_int("mqttlost", self.get_connlost_count() + 1)

    def reset_connlost_count(self):
        self.net.set_nvram_int("mqttlost", 0)

    def pub(self, pubobj):
        pubobj.adjust_topic(self.name)
        self.publist.append(pubobj)
        return pubobj

    def sub(self, subobj):
        subobj.adjust_topic(self.name)
        self.sublist[subobj.topic] = subobj
        return subobj

    def on_start(self):
        self.last_communication = Shortcronometer()
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

        self.disconn_backoff = (self.disconn_backoff * 3) // 2
        if self.last_communication.elapsed() > 10 * MINUTES:
            loop.reboot("Too much time w/o MQTT connection, rebooting")

        self.sm.schedule_trans_now("connlost")

    def on_connected(self):
        self.disconn_backoff = 500 * MILISSECONDS
        self.last_communication = Shortcronometer()

        self.ping_task = self.sm.recurring_task("mqtt_ping", self.ping, 20 * SECONDS, fudge=10 * SECONDS)
        self.sm.poll_object("mqtt_sock", self.impl.sock, POLLIN, self.eval_sub)
        self.sm.onetime_task("mqtt_pub", self.eval_pub, 0)

    def received_data(self, topic, msg, retained, dup):
        self.last_communication = Shortcronometer()
        if topic in self.sublist:
            self.sublist[topic].recv(topic, msg, retained, dup)
        else:
            print("MQTT recv invalid topic", topic)

    def ping(self, _):
        self.watchdog.may_block()
        try:
            self.impl.ping()
            self.last_communication = Shortcronometer()
            # print("MQTT ping")
        except (MQTTException, OSError):
            print("MQTT conn fail at ping")
            self.incr_connlost_count()
            self.sm.schedule_trans_now("connlost")
        finally:
            self.watchdog.may_block_exit()

    def on_connlost(self):
        self.disconnect()
        self.sm.schedule_trans("testnet", self.disconn_backoff, fudge=self.disconn_backoff // 2)

    def eval_sub(self, _):
        try:
            self.impl.check_msg()
            self.last_communication = Shortcronometer()
        except (MQTTException, OSError):
            print("MQTT conn fail at check_msg")
            self.incr_connlost_count()
            self.sm.schedule_trans_now("connlost")
            return

    def pub_requested(self, pubobj):
        if self.sm.state == 'connected' and not self.pub_pending:
            self.sm.onetime_task("mqtt_pub", self.eval_pub, 0)
        if pubobj not in self.pub_pending:
            self.pub_pending.append(pubobj)

    def refresh_all_pubs(self):
        for pubobj in self.publist:
            self.pub_requested(pubobj)

    def eval_pub(self, _):
        if self.sm.state != 'connected' or not self.pub_pending:
            return

        pubobj, self.pub_pending = self.pub_pending[0], self.pub_pending[1:]

        self.watchdog.may_block() # impl.publish() may block
        try:
            if pubobj.msg is not None:
                self.impl.publish(pubobj.topic, pubobj.msg, pubobj.retain)
                print("MQTT pub %s %s" % (pubobj.topic, pubobj.msg))
                self.last_communication = Shortcronometer()
                self.ping_task.restart()
            if self.pub_pending:
                self.sm.onetime_task("mqtt_pub", self.eval_pub, 0)
        except (MQTTException, OSError):
            print("MQTT conn fail at pub")
            self.incr_connlost_count()
            self.sm.schedule_trans_now("connlost")
        finally:
            self.watchdog.may_block_exit()

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
        self.retain = retain
        self.forcepubtask = None
        if to > 0:
            Task(True, "eval_%s" % topic, self.eval, to).advance()
        if forcepubto > 0:
            self.forcepubtask = Task(True, "force_%s" % topic, self.forcepub, forcepubto)

    def adjust_topic(self, name):
        self.topic = self.topic % name.encode('ascii')

    # May be called manually
    def forcepub(self, _=None):
        self.eval(_, True)

    # May be overridden
    def pub_condition(self, force, oldmsg, newmsg):
        return force or oldmsg != newmsg

    def eval(self, _, force=False):
        new_msg = self.gen_msg()
        if new_msg is not None:
            new_msg = new_msg.encode('utf-8')
            # FIXME clarify semantics - if a topic generates 'None', does this mean
            # a) no change, or b) cease to publish?
        if self.pub_condition(force, self.msg, new_msg):
            self.msg = new_msg
            if self.msg is not None:
                mqtt_manager.pub_requested(self)
                if self.forcepubtask:
                    self.forcepubtask.restart()

    def gen_msg(self): # override
        self.msg = None # pragma: no cover


class MQTTSub:
    def __init__(self, topic):
        self.topic = topic.encode('ascii')

    def adjust_topic(self, name):
        self.topic = self.topic % name.encode('ascii')

    def recv(self, topic, msg, retained, dup): # override
        pass # pragma: no cover


class Log(MQTTPub):
    def __init__(self, mqttmanager):
        MQTTPub.__init__(self, "stat/%s/Log", 0, 0, False)
        self.logmsg = None
        self.mqttmanager = mqttmanager

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

    def dumpstats(self):
        net_connlost_count = self.mqttmanager.net.get_connlost_count()
        mqtt_connlost_count = self.mqttmanager.get_connlost_count()
        self.logmsg = 'connlost events net %d mqtt %d' % (net_connlost_count, mqtt_connlost_count)
        self.forcepub()

    def resetstats(self):
        self.mqttmanager.net.reset_connlost_count()
        self.mqttmanager.reset_connlost_count()
        self.logmsg = 'stats resetted'
        self.forcepub()

    def dumpmsg(self, msg):
        self.logmsg = msg
        self.forcepub()

    def getversion(self):
        self.logmsg = str(os.uname())
        self.forcepub()


# TODO allow to decrease how often it is pinged
class Uptime(MQTTPub):
    def __init__(self):
        MQTTPub.__init__(self, "stat/%s/Uptime", 60 * SECONDS, 30 * MINUTES, False)
        self.uptime = Longcronometer()

    def gen_msg(self):
        return "%d" % (self.uptime.elapsed() // MINUTES)


class Refresh(MQTTSub):
    def __init__(self):
        MQTTSub.__init__(self, "cmnd/%s/Refresh")

    def recv(self, topic, msg, retained, dup):
        if retained or dup or not msg:
            return
        mqtt_manager.refresh_all_pubs()
