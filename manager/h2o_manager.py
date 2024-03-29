#!/usr/bin/env python3 

import os, sys
import time
import paho.mqtt.client as mqtt
from myeventloop import EventLoop, Log, Timeout
from myeventloop.queue import Queue
from myeventloop.statemachine import StateMachine

Log.set_level(Log.DEBUG)

MQTT_HOST = sys.argv[1]
MQTT_PORT = 1883
under_test = "--test" in sys.argv
alaw = "--alternate-law" in sys.argv

H2O = "H2OControl"
RELAY = "RelayControl"
MY_MQTT_PREFIX = 'H2OManager'

TOPICS = [('stat/%s/#' % H2O, 2), ('stat/%s/#' % RELAY, 2), ('cmnd/%s/#' % MY_MQTT_PREFIX, 2)]

MQTT_CLIENT_ID = "%s" % MY_MQTT_PREFIX
MQTT_MANUALOFF = "cmnd/%s/ManualOff" % MY_MQTT_PREFIX
MQTT_MANUALON = "cmnd/%s/ManualOn" % MY_MQTT_PREFIX
MQTT_SM_STATE = "stat/%s/State" % MY_MQTT_PREFIX
MQTT_WARNING = "stat/%s/Warning" % MY_MQTT_PREFIX
MQTT_UPTIME = "stat/%s/Uptime" % MY_MQTT_PREFIX
PERSIST_MANUALOFF = "manualoff.txt"

MQTT_PUMP = "cmnd/%s/0/TurnOnWithTimeout" % RELAY

LEVEL_LOW_THRESHOLD = 80.0 - 0.01
LEVEL_FULL_THRESHOLD = 100.0 - 0.01

TANK_CAPACITY = 1000.0 # L
EXPECTED_FLOW = 13.0 # L/min

TOPPING_VOLUME = TANK_CAPACITY * (LEVEL_FULL_THRESHOLD - LEVEL_LOW_THRESHOLD) / 100.0 * 1.2
TOPPING_MINIMUM_TIME = 60 # s
TOPPING_TIME_ALAW = TOPPING_VOLUME / EXPECTED_FLOW * 60 # (L / L/min) -> min -> s
TOPPING_DELAY = 24.0 * 60 * 60 # h -> s
if under_test:
    TOPPING_TIME_ALAW = 60
    TOPPING_DELAY = 30
    TOPPING_MINIMUM_TIME = 10

PIPE_LENGTH = 75.0 # m
PIPE_DIAMETER = 25.0 / 1000.0 # m
PIPE_RADIUS = PIPE_DIAMETER / 2.0 # m
PIPE_AREA = PIPE_RADIUS * PIPE_RADIUS * 3.14159 # m2
PIPE_CAPACITY = PIPE_LENGTH * PIPE_AREA * 1000.0 # m3 -> L

RESTING_TIME = 4.0 * 60 # min -> sec
if under_test:
    RESTING_TIME = 0.5 * 60

# Not used
PIPE_FILL_TIMEOUT = (2.0 * PIPE_CAPACITY / EXPECTED_FLOW) * 60 # min -> sec

LOWFLOW_THRESHOLD = 0.25 * EXPECTED_FLOW # L/min
LOWFLOW_TIMEOUT = 2.0 * 60 #  min -> sec
LOWFLOW_RECOVER = 12.0 * 60 * 60 # h -> sec
if under_test:
    LOWFLOW_TIMEOUT = 1.0 * 60
    LOWFLOW_RECOVER = 2.0 * 60

PUMP_TIMEOUT = (1.2 * TANK_CAPACITY / EXPECTED_FLOW) * 60 # min -> sec
PUMPTIMEOUT_RECOVER = 24.0 * 60 * 60 # h -> sec
if under_test:
    PUMP_TIMEOUT = 2.0 * 60
    PUMPTIMEOUT_RECOVER = 2.0 * 60

MANUALON_TIMEOUT = 30.0 * 60 # min -> sec

def start_mqtt(queue):
    mqtt_client = mqtt.Client(MQTT_CLIENT_ID)

    def on_connect(mqtt_client, _, flags, conn_result):
        Log.debug2("MQTT connected")
        mqtt_client.subscribe(TOPICS)
    mqtt_client.on_connect = on_connect

    def on_message(mqtt_client, queue, mqttmsg):
        topic = mqttmsg.topic
        message = mqttmsg.payload.decode('utf-8')
        Log.debug2("MQTT msg %s %s" % (topic, message))
        queue.push(topic, message)
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_HOST, MQTT_PORT)
    mqtt_client.user_data_set(queue)
    mqtt_client.loop_start() # starts thread

    return mqtt_client


class WaterStateMachine(StateMachine):
    def __init__(self, queue, mqttsm, mqtt_client):
        super().__init__("water")

        self.never_full_events = 0
        self.q = queue
        self.mqttsm = mqttsm
        self.mqtt_client = mqtt_client
        self.add_queue(queue)
        self.add_sm(mqttsm)

        self.add_state("nomqtt", self.to_nomqtt)
        self.add_state("off", self.to_off)
        self.add_state("manualoff", self.to_manualoff)
        self.add_state("on", self.to_on)
        self.add_state("manualon", self.to_manualon)
        self.add_state("rest", self.to_rest)
        self.add_state("lowflow", self.to_lowflow)
        self.add_state("timeout", self.to_timeout)
        self.add_state("malfunction", self.to_malfunction)

        # Ordinary sequence
        self.add_transition("initial", "nomqtt")
        self.add_transition("nomqtt", "off")
        self.add_transition("off", "on")
        self.add_transition("on", "rest")
        self.add_transition("rest", "off")

        # Failures
        self.add_transition("on", "lowflow")
        self.add_transition("on", "timeout")
        self.add_transition("on", "malfunction")
        self.add_transition("off", "malfunction")
        # Failure resolution
        self.add_transition("lowflow", "off")
        self.add_transition("timeout", "off")
        self.add_transition("malfunction", "off")

        # Respect 'timeout' and 'rest' even if MQTT goes dark
        self.add_transition("off", "nomqtt")
        self.add_transition("manualoff", "nomqtt")
        self.add_transition("on", "nomqtt")
        self.add_transition("manualon", "noqmtt")
        self.add_transition("malfunction", "noqmtt")

        # All states except "manual off" can go to "manual on"
        self.add_transition("off", "manualon")
        self.add_transition("on", "manualon")
        self.add_transition("rest", "manualon")
        self.add_transition("lowflow", "manualon")
        self.add_transition("timeout", "manualon")
        self.add_transition("manualon", "rest") # Only exit

        # Any state can go to "manualoff"
        self.add_transition("off", "manualoff")
        self.add_transition("on", "manualoff")
        self.add_transition("manualon", "manualoff")
        self.add_transition("rest", "manualoff")
        self.add_transition("lowflow", "manualoff")
        self.add_transition("timeout", "manualoff")
        self.add_transition("manualoff", "off") # Only exit

        # FIXME generate graph and/or autotest for state machine

    def publish_state(self, state_name):
        def republish(task):
            self.mqtt_client.publish(MQTT_SM_STATE, state_name)
            task.reset(600)
        self.timeout("publish_state", 0, republish)

    def pump_on(self):
        def keep_on(task):
            Log.info("Pump on")
            self.mqtt_client.publish(MQTT_PUMP, "60")
            task.reset(15)
        self.timeout("pump_on", 0, keep_on)

    def pump_off(self):
        self.mqtt_client.publish(MQTT_PUMP, "0")
        Log.info("Pump off")

    def to_nomqtt(self):
        self.publish_state("Offline")

        def on_conn():
            Log.info("MQTT connected to controllers")
            self.schedule_trans("off", 5.0)
        self.mqttsm.observe(self, "a", "connected", on_conn)

    def detect_nomqtt(self):
        def on_disconn():
            self.trans_now("nomqtt")
        self.mqttsm.observe(self, "a", "!connected", on_disconn)

    def persist_manualoff(self):
        open(PERSIST_MANUALOFF, "w").close()
        print("Persisted manual-off state")

    def unpersist_manualoff(self):
        try:
            os.unlink(PERSIST_MANUALOFF)
            print("Unpersisted manual-off state")
        except FileNotFoundError:
            print("Did not need to unpersist manual-off state")

    def detect_manualoff(self):
        def on_msg(n):
            if n == 1:
                self.trans_now("manualoff")
        self.q.on_int(self, MQTT_MANUALOFF, on_msg, True)

        def check_manualoff_persist(_):
            if os.path.exists(PERSIST_MANUALOFF):
                print("Detected persisted manual-off state")
                self.trans_now("manualoff")
        self.timeout("check_manualoff_persist", 0, check_manualoff_persist)

    def detect_manualon(self):
        def on_msg(n):
            if n == 1:
                self.trans_now("manualon")
        self.q.on_int(self, MQTT_MANUALON, on_msg, True)

    def detect_malfunction(self):
        def on_msg(n):
            if n > 0:
                self.mqtt_client.publish(MQTT_WARNING, "Sensor malfunction %d" % n)
                self.trans_now("malfunction")
        self.q.on_int(self, "stat/%s/Malfunction" % H2O, on_msg, True)

    # Informative only
    def log_tanklevel(self):
        def on_levelstr(s):
            Log.info("Tank level str %s" % s)
        self.q.on_msg(self, "stat/%s/EstimatedLevelStr" % H2O, on_levelstr, True)

    def to_off(self):
        self.publish_state("Off")
        self.pump_off()

        self.detect_nomqtt()
        self.detect_manualon()
        self.detect_manualoff()
        self.detect_malfunction()
        self.log_tanklevel()

        self.topping_delay = None

        def on_level(level):
            if level < LEVEL_LOW_THRESHOLD:
                # e.g. < 80%
                Log.info("Level below threshold")
                self.trans_now("on")
            elif level < LEVEL_FULL_THRESHOLD:
                # e.g. between 80% and 100%
                if not self.topping_delay:
                    Log.info("Level almost full - timeout started")
                    self.topping_delay = self.schedule_trans("on", TOPPING_DELAY)
            else:
                # 100%
                self.never_full_events = 0
                if self.topping_delay:
                    Log.info("Cancelling almost-full timeout")
                    self.topping_delay.cancel()
                    self.topping_delay = None

        self.q.on_float(self, "stat/%s/CoarseLevelPct" % H2O, on_level, True)

    def to_on(self):
        self.publish_state("On")
        self.pump_on()

        self.detect_nomqtt()
        self.detect_manualon()
        self.detect_manualoff()
        self.detect_malfunction()
        self.log_tanklevel()

        # Safety measure in case of severe leaking

        self.schedule_trans("timeout", PUMP_TIMEOUT)

        # Safety measure in case of dry pump

        if alaw:
            Log.info("(Alternate law - not monitoring flow)")
        else:
            lowflow_task = self.schedule_trans("lowflow", LOWFLOW_TIMEOUT)

            def on_flow(flow):
                if flow <= LOWFLOW_THRESHOLD:
                    return
                if not on_flow.logged:
                    Log.info("Flow detected")
                    on_flow.logged = True
                lowflow_task.restart()
            on_flow.logged = False

            self.q.on_float(self, "stat/%s/Flow" % H2O, on_flow, True)

        # Monitor level changes

        def on_level(level):
            Log.info("Tank level %f" % level)

            # Tank quite empty
            if level < LEVEL_LOW_THRESHOLD:
                cancel_almost_full(level)
                return

            # Tank full
            if level >= LEVEL_FULL_THRESHOLD:
                Log.info("Level is full")
                self.never_full_events = 0
                self.trans_now("rest")
                return

            # Tank almost full: special handling
            almost_full(level)

        self.q.on_float(self, "stat/%s/CoarseLevelPct" % H2O, on_level, True)

        # Monitor volume pumped

        self.pumped_volume_0 = None
        self.pumped_volume = None

        def net_pumped_volume():
            if self.pumped_volume_0 is None:
                return 0.0
            return self.pumped_volume - self.pumped_volume_0

        def on_pumped(vol):
            self.pumped_volume = vol
            if self.pumped_volume_0 is None or vol < self.pumped_volume_0:
                # First sample, or coarse level has changed
                self.pumped_volume_0 = vol
            netvol = net_pumped_volume()
            Log.info("Pumped volume after level change: %f (net %f)" % (vol, netvol))

        self.q.on_float(self, "stat/%s/PumpedAfterLevelChange" % H2O, on_pumped, True)

        ####### Special handling for almost-full tank

        self.almost_full_timer = None

        # Almost-full logic, entry point

        def almost_full(level):
            # 1st or 2nd stage timer already installed
            if self.almost_full_timer:
                return

            # 1st stage: wait a minimum time before taking any decision
            def f(_):
                almost_full_2nd(level)
            self.almost_full_timer = self.timeout("almost_full_pre", TOPPING_MINIMUM_TIME, f)

        # Cancel almost-full timer (e.g. if level recedes to <80%)

        def cancel_almost_full(level):
            if self.almost_full_timer:
                self.almost_full_timer.cancel()
                self.almost_full_timer = None

        # Almost-full logic, 2nd stage, called after TOPPING_MINIMUM_TIME

        def almost_full_2nd(level):
            if alaw:
                almost_full_alaw(level)
            else:
                almost_full_regular(level)

        # Almost-full logic: basic time-based protection against overflow for alternate law

        def almost_full_alaw(level):
            def timeout(task):
                # It was expected that tank was full by this time
                Log.info("Pumped topping volume (estimated)")
                self.never_full_events += 1
                if self.never_full_events >= 3:
                    self.mqtt_client.publish(MQTT_WARNING, "Stopped after pumping (estimated) topping volume")
                self.trans_now("rest")
 
            self.almost_full_timer = self.timeout("almost_full", TOPPING_TIME_ALAW - TOPPING_MINIMUM_TIME, timeout)

        # Almost-full logic: volume-based protection against overflow

        def almost_full_regular(level):
            def timeout(task):
                if net_pumped_volume() > TOPPING_VOLUME:
                    # It was expected that level went 100% after so much volume pumped
                    Log.info("Pumped topping volume")
                    self.never_full_events += 1
                    if self.never_full_events >= 3:
                        self.mqtt_client.publish(MQTT_WARNING, "Stopped after pumping topping volume")
                    self.trans_now("rest")
                    return
                task.restart()

            self.almost_full_timer = self.timeout("almost_full", 15, timeout)

    def to_manualon(self):
        self.publish_state("ManualOn")
        self.pump_on()

        self.detect_nomqtt()
        self.detect_manualoff()
        auto_off = self.schedule_trans("rest", MANUALON_TIMEOUT)

        def on_msg(n):
            if n == 1:
                auto_off.restart()
            else:
                self.trans_now("rest")
        self.q.on_int(self, MQTT_MANUALON, on_msg, True)

    def to_manualoff(self):
        self.persist_manualoff()
        self.publish_state("ManualOff")
        self.pump_off()
        self.detect_nomqtt()

        def on_msg(n):
            if n != 1:
                self.unpersist_manualoff()
                self.trans_now("off")
        self.q.on_int(self, MQTT_MANUALOFF, on_msg, True)

    def to_rest(self):
        self.publish_state("Resting")
        self.pump_off()

        self.detect_manualon()
        self.detect_manualoff()
        self.schedule_trans("off", RESTING_TIME)

    def to_lowflow(self):
        self.publish_state("LowFlowError")
        self.mqtt_client.publish(MQTT_WARNING, "Low flow, stopping pump")
        self.pump_off()

        self.detect_manualon()
        self.detect_manualoff()
        self.schedule_trans("off", LOWFLOW_RECOVER)

    def to_timeout(self):
        self.publish_state("TimeoutError")
        self.mqtt_client.publish(MQTT_WARNING, "Timeout, stopping pump")
        self.pump_off()
        
        self.detect_manualon()
        self.detect_manualoff()
        self.schedule_trans("off", PUMPTIMEOUT_RECOVER)

    def to_malfunction(self):
        self.publish_state("Malfunction")
        self.pump_off()

        self.detect_nomqtt()

        def on_msg(n):
            if n == 0:
                self.trans_now("off")
        self.q.on_int(self, "stat/%s/Malfunction" % H2O, on_msg, True)


class MQTTStateMachine(StateMachine):
    def __init__(self, h2osm, relaysm):
        super().__init__("mqttsm")

        self.add_state("disconnected", self.to_disconnected)
        self.add_state("connecting", self.to_connecting)
        self.add_state("connected", self.to_connected)
        self.add_transition("initial", "disconnected")
        self.add_transition("disconnected", "connecting")
        self.add_transition("connecting", "disconnected")
        self.add_transition("connecting", "connected")
        self.add_transition("connected", "disconnected")

        self.h2osm = h2osm
        self.relaysm = relaysm

        self.add_sm(h2osm)
        self.add_sm(relaysm)

    def to_disconnected(self):
        def on_change():
            self.trans_now("connecting")
        self.h2osm.observe(self, "a", "connected", on_change)

    def to_connecting(self):
        def on_change():
            self.trans_now("connected")
        self.relaysm.observe(self, "a", "connected", on_change)

    def to_connected(self):
        def on_change():
            self.trans_now("disconnected")
            
        self.h2osm.observe(self, "a", "!connected", on_change)
        self.relaysm.observe(self, "a", "!connected", on_change)


class UptimeStateMachine(StateMachine):
    def __init__(self, prefix, queue):
        super().__init__("uptime_%s" % prefix)
        self.prefix = prefix

        self.add_state("disconnected", self.to_disconnected)
        self.add_state("connecting", self.to_connecting)
        self.add_state("connected", self.to_connected)

        self.add_transition("initial", "disconnected")
        self.add_transition("disconnected", "connecting")
        self.add_transition("connecting", "disconnected")
        self.add_transition("connecting", "connected")
        self.add_transition("connected", "disconnected")

        self.add_queue(queue)
        self.q = queue

    def to_disconnected(self):
        self.uptime = -1

        def on_uptime(new_uptime):
            Log.debug2("on_uptime d")
            if new_uptime >= 0:
                self.uptime = new_uptime
                self.trans_now("connecting")

        self.q.on_int(self, "stat/%s/Uptime" % self.prefix, on_uptime, True)

    def to_connecting(self):
        self.schedule_trans("disconnected", 1.5 * 60)

        def on_uptime(new_uptime):
            Log.debug2("on_uptime c1")
            if new_uptime >= 0 and new_uptime != self.uptime:
                self.uptime = new_uptime
                self.trans_now("connected")

        self.q.on_int(self, "stat/%s/Uptime" % self.prefix, on_uptime, True)

    def to_connected(self):
        to_task = self.schedule_trans("disconnected", 2.5 * 60)

        def on_uptime(new_uptime):
            Log.debug2("on_uptime c2 %d" % new_uptime)
            if new_uptime >= 0 and new_uptime != self.uptime:
                self.uptime = new_uptime
                to_task.restart()

        self.q.on_int(self, "stat/%s/Uptime" % self.prefix, on_uptime, True)
        

loop = EventLoop()
mqttqueue = Queue("mqtt")
h2o_uptime_sm = UptimeStateMachine(H2O, mqttqueue)
relay_uptime_sm = UptimeStateMachine(RELAY, mqttqueue)
mqtt_sm = MQTTStateMachine(h2o_uptime_sm, relay_uptime_sm)
mqtt_client = start_mqtt(mqttqueue)
water_sm = WaterStateMachine(mqttqueue, mqtt_sm, mqtt_client)
h2o_uptime_sm.trans_now("disconnected")
relay_uptime_sm.trans_now("disconnected")
mqtt_sm.trans_now("disconnected")
water_sm.trans_now("nomqtt")

startup = time.time()

def report_uptime(task):
    uptime_minutes = (time.time() - startup) // 60
    mqtt_client.publish(MQTT_UPTIME, "%d" % uptime_minutes)
    task.restart()

uptime_to = Timeout.new("report_uptime", 60, report_uptime)

try:
    loop.loop()
except KeyboardInterrupt:
    Log.warn("Stopping MQTT...")
    mqtt_client.loop_stop()
    Log.warn("Exiting...")
    sys.exit(0)
