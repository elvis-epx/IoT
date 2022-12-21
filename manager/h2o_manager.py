#!/usr/bin/env python3 

import os, sys
from time import time
import paho.mqtt.client as mqtt
from myeventloop import EventLoop, Log, Timeout
from myeventloop.queue import Queue
from myeventloop.statemachine import StateMachine

Log.set_level(Log.DEBUG)

MQTT_HOST = sys.argv[1]
MQTT_PORT = 1883
under_test = len(sys.argv) > 2 and sys.argv[2] == "--test"

H2O = "H2OControl"
RELAY = "RelayControl"
MY_MQTT_PREFIX = 'H2OManager'

TOPICS = [('stat/%s/#' % H2O, 2), ('stat/%s/#' % RELAY, 2), ('cmnd/%s/#' % MY_MQTT_PREFIX, 2)]

MQTT_CLIENT_ID = "%s" % MY_MQTT_PREFIX
MQTT_MANUALOFF = "cmnd/%s/ManualOff" % MY_MQTT_PREFIX
MQTT_MANUALON = "cmnd/%s/ManualOn" % MY_MQTT_PREFIX
MQTT_STATE = "stat/%s/State" % MY_MQTT_PREFIX

MQTT_PUMP = "cmnd/%s/0/TurnOnWithTimeout" % RELAY

LEVEL_LOW_THRESHOLD = 80.0 - 0.2
LEVEL_FULL_THRESHOLD = 100.0 - 0.1

TANK_CAPACITY = 1000.0 # L
EXPECTED_FLOW = 13.0 # L/min

PIPE_LENGTH = 75.0 # m
PIPE_DIAMETER = 25.0 / 1000.0 # m
PIPE_RADIUS = PIPE_DIAMETER / 2.0 # m
PIPE_AREA = PIPE_RADIUS * PIPE_RADIUS * 3.14159 # m2
PIPE_CAPACITY = PIPE_LENGTH * PIPE_AREA * 1000.0 # m3 -> L

RESTING_TIME = 2.0 * 60 # min -> sec
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

PUMP_TIMEOUT = (1.5 * TANK_CAPACITY / EXPECTED_FLOW) * 60 # min -> sec
PUMPTIMEOUT_RECOVER = 12.0 * 60 * 60 # h -> sec
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

        self.q = queue
        self.mqttsm = mqttsm
        self.mqtt_client = mqtt_client
        self.add_queue(queue)
        self.add_sm(mqttsm)

        self.add_state("nomqtt", self.on_nomqtt)
        self.add_state("off", self.on_off)
        self.add_state("manualoff", self.on_manualoff)
        self.add_state("on", self.on_on)
        self.add_state("manualon", self.on_manualon)
        self.add_state("rest", self.on_rest)
        self.add_state("lowflow", self.on_lowflow)
        self.add_state("timeout", self.on_timeout)
        self.add_state("malfunction", self.on_malfunction)

        # Ordinary sequence
        self.add_transition("initial", "nomqtt")
        self.add_transition("nomqtt", "off")
        self.add_transition("off", "on")
        self.add_transition("on", "rest")
        self.add_transition("rest", "off")

        # Failures
        self.add_transition("on", "lowflow")
        self.add_transition("on", "timeout")
        # Failure resolution
        self.add_transition("lowflow", "off")
        self.add_transition("timeout", "off")

        self.add_transition("off", "nomqtt")
        self.add_transition("manualoff", "nomqtt")
        self.add_transition("on", "nomqtt")
        self.add_transition("manualon", "noqmtt")
        self.add_transition("malfunction", "noqmtt")

        # All states except "manual off" can go to "manual on"
        self.add_transition("on", "manualon")
        self.add_transition("off", "manualon")
        self.add_transition("rest", "manualon")
        self.add_transition("lowflow", "manualon")
        self.add_transition("timeout", "manualon")
        # Only exit from "manualon", apart from MQTT disconnection
        self.add_transition("manualon", "rest")

        # Any state can go to "manualoff"
        self.add_transition("off", "manualoff")
        self.add_transition("on", "manualoff")
        self.add_transition("manualon", "manualoff")
        self.add_transition("rest", "manualoff")
        self.add_transition("lowflow", "manualoff")
        self.add_transition("timeout", "manualoff")
        # Only exit from "manualoff", apart from MQTT disconnection
        self.add_transition("manualoff", "off")

        self.add_transition("off", "malfunction")
        self.add_transition("on", "malfunction")
        self.add_transition("malfunction", "off")

    def pump_on(self):
        def keep_on(task):
            Log.info("Pump on")
            self.mqtt_client.publish(MQTT_PUMP, "60")
            task.reset(15)
        self.timeout("pump_on", 0, keep_on)

    def pump_off(self):
        self.mqtt_client.publish(MQTT_PUMP, "0")
        Log.info("Pump off")

    def on_nomqtt(self):
        self.mqtt_client.publish(MQTT_STATE, "Offline")

        def on_conn():
            Log.info("MQTT connected to controllers")
            self.schedule_trans("off", 5.0)
        self.mqttsm.observe(self, "a", "connected", on_conn)

    def detect_nomqtt(self):
        def on_disconn():
            self.trans_now("nomqtt")
        self.mqttsm.observe(self, "a", "!connected", on_disconn)

    def detect_manualoff(self):
        def on_msg(n):
            if n == 1:
                self.trans_now("manualoff")
        self.q.on_int(self, MQTT_MANUALOFF, on_msg, True)

    def detect_manualon(self):
        def on_msg(n):
            if n == 1:
                self.trans_now("manualon")
        self.q.on_int(self, MQTT_MANUALON, on_msg, True)

    def detect_malfunction(self):
        def on_msg(n):
            if n > 0:
                self.trans_now("malfunction")
        self.q.on_int(self, "stat/%s/Malfunction" % H2O, on_msg, True)

    # Informative only
    def log_tanklevel(self):
        def on_levelstr(s):
            Log.info("Tank level %s" % s)
        self.q.on_msg(self, "stat/%s/EstimatedLevelStr" % H2O, on_levelstr, True)

    def on_off(self):
        self.mqtt_client.publish(MQTT_STATE, "Off")
        self.pump_off()

        self.detect_nomqtt()
        self.detect_manualon()
        self.detect_manualoff()
        self.detect_malfunction()
        self.log_tanklevel()

        def on_level(level):
            if level < LEVEL_LOW_THRESHOLD:
                Log.info("Level below threshold")
                self.trans_now("on")
        self.q.on_float(self, "stat/%s/CoarseLevelPct" % H2O, on_level, True)

    def on_on(self):
        self.mqtt_client.publish(MQTT_STATE, "On")
        self.pump_on()

        self.detect_nomqtt()
        self.detect_manualon()
        self.detect_manualoff()
        self.detect_malfunction()
        self.log_tanklevel()

        def on_level(level):
            Log.info("Tank level %f" % level)
            if level >= LEVEL_FULL_THRESHOLD:
                Log.info("Level is full")
                self.trans_now("rest")
        self.q.on_float(self, "stat/%s/CoarseLevelPct" % H2O, on_level, True)

        # Safety measure in case of dry pump
        lowflow_task = self.schedule_trans("lowflow", LOWFLOW_TIMEOUT)
        # Safety measure in case of leaking
        self.schedule_trans("timeout", PUMP_TIMEOUT)

        def on_flow(flow):
            if flow > LOWFLOW_THRESHOLD:
                if on_flow.virgin:
                    Log.info("Flow detected")
                    on_flow.virgin = False
                lowflow_task.restart()
        on_flow.virgin = True
        self.q.on_float(self, "stat/%s/Flow" % H2O, on_flow, True)

    def on_manualon(self):
        self.mqtt_client.publish(MQTT_STATE, "ManualOn")
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

    def on_manualoff(self):
        self.mqtt_client.publish(MQTT_STATE, "ManualOff")
        self.pump_off()
        self.detect_nomqtt()

        def on_msg(n):
            if n != 1:
                self.trans_now("off")
        self.q.on_int(self, MQTT_MANUALOFF, on_msg, True)

    def on_rest(self):
        self.mqtt_client.publish(MQTT_STATE, "Resting")
        self.pump_off()

        self.detect_manualon()
        self.detect_manualoff()
        self.schedule_trans("off", RESTING_TIME)

    def on_lowflow(self):
        self.mqtt_client.publish(MQTT_STATE, "LowFlowError")
        self.pump_off()

        self.detect_manualon()
        self.detect_manualoff()
        self.schedule_trans("off", LOWFLOW_RECOVER)

    def on_timeout(self):
        self.mqtt_client.publish(MQTT_STATE, "TimeoutError")
        self.pump_off()
        
        self.detect_manualon()
        self.detect_manualoff()
        self.schedule_trans("off", PUMPTIMEOUT_RECOVER)

    def on_malfunction(self):
        self.mqtt_client.publish(MQTT_STATE, "Malfunction")
        self.pump_off()

        self.detect_nomqtt()

        def on_msg(n):
            if n == 0:
                self.trans_now("off")
        self.q.on_int(self, "stat/%s/Malfunction" % H2O, on_msg, True)


class MQTTStateMachine(StateMachine):
    def __init__(self, h2osm, relaysm):
        super().__init__("mqttsm")

        self.add_state("disconnected", self.on_disconnected)
        self.add_state("connecting", self.on_connecting)
        self.add_state("connected", self.on_connected)
        self.add_transition("initial", "disconnected")
        self.add_transition("disconnected", "connecting")
        self.add_transition("connecting", "disconnected")
        self.add_transition("connecting", "connected")
        self.add_transition("connected", "disconnected")

        self.h2osm = h2osm
        self.relaysm = relaysm

        self.add_sm(h2osm)
        self.add_sm(relaysm)

    def on_disconnected(self):
        def on_change():
            self.trans_now("connecting")
        self.h2osm.observe(self, "a", "connected", on_change)

    def on_connecting(self):
        def on_change():
            self.trans_now("connected")
        self.relaysm.observe(self, "a", "connected", on_change)

    def on_connected(self):
        def on_change():
            self.trans_now("disconnected")
            
        self.h2osm.observe(self, "a", "!connected", on_change)
        self.relaysm.observe(self, "a", "!connected", on_change)


class UptimeStateMachine(StateMachine):
    def __init__(self, prefix, queue):
        super().__init__("uptime_%s" % prefix)
        self.prefix = prefix

        self.add_state("disconnected", self.on_disconnected)
        self.add_state("connecting", self.on_connecting)
        self.add_state("connected", self.on_connected)

        self.add_transition("initial", "disconnected")
        self.add_transition("disconnected", "connecting")
        self.add_transition("connecting", "disconnected")
        self.add_transition("connecting", "connected")
        self.add_transition("connected", "disconnected")

        self.add_queue(queue)
        self.q = queue

    def on_disconnected(self):
        self.uptime = -1

        def on_uptime(new_uptime):
            Log.debug2("on_uptime d")
            if new_uptime >= 0:
                self.uptime = new_uptime
                self.trans_now("connecting")

        self.q.on_int(self, "stat/%s/Uptime" % self.prefix, on_uptime, True)

    def on_connecting(self):
        self.schedule_trans("disconnected", 1.5 * 60)

        def on_uptime(new_uptime):
            Log.debug2("on_uptime c1")
            if new_uptime >= 0 and new_uptime != self.uptime:
                self.uptime = new_uptime
                self.trans_now("connected")

        self.q.on_int(self, "stat/%s/Uptime" % self.prefix, on_uptime, True)

    def on_connected(self):
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

try:
    loop.loop()
except KeyboardInterrupt:
    Log.warn("Stopping MQTT...")
    mqtt_client.loop_stop()
    Log.warn("Exiting...")
    sys.exit(0)