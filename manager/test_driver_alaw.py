#!/usr/bin/env python3 

import os, sys
from time import time
import paho.mqtt.client as mqtt
from myeventloop import EventLoop, Log, Timeout

Log.set_level(Log.DEBUG)

H2O_PREFIX = "stat/H2OControl/"
H2O_CPREFIX = "cmnd/H2OManager/"
RELAY_PREFIX = "stat/RelayControl/"
MQTT_STATE = "stat/H2OManager/State"
TOPICS = [(MQTT_STATE, 2)]

ctx = {'sm': ''}

def start_mqtt():
    mqtt_client = mqtt.Client("Test driver")

    def on_connect(mqtt_client, _, flags, conn_result):
        Log.debug2("driver: MQTT connected")
        mqtt_client.subscribe(TOPICS)
    mqtt_client.on_connect = on_connect

    def on_message(mqtt_client, _, mqttmsg):
        topic = mqttmsg.topic
        message = mqttmsg.payload.decode('utf-8')
        Log.debug("driver: MQTT msg %s %s" % (topic, message))
        if topic == MQTT_STATE:
            ctx['sm'] = message
    mqtt_client.on_message = on_message

    mqtt_client.connect('127.0.0.1', 1883)
    mqtt_client.user_data_set(None)
    mqtt_client.loop_start() # starts thread

    return mqtt_client

def sim_h2o_uptime(task):
    Log.info("driver: sim_h2o_uptime")
    mqtt_client.publish(H2O_PREFIX + "Uptime", sim_h2o_uptime.n)
    sim_h2o_uptime.n += 1
    task.restart()
sim_h2o_uptime.n = 0

def sim_relay_uptime(task):
    Log.info("driver: sim_relay_uptime")
    mqtt_client.publish(RELAY_PREFIX + "Uptime", sim_relay_uptime.n)
    sim_relay_uptime.n += 1
    task.restart()
sim_relay_uptime.n = 0

######################################################## Test modules

def assert_offline(_):
    Log.info("driver: assert_offline")
    assert ctx['sm'] == "Offline"
    # Simulate Uptime messages that indicate that sensors are online
    ctx['h2o_uptime_task'] = Timeout.new("h2o_uptime", 10, sim_h2o_uptime)
    ctx['relay_uptime_task'] = Timeout.new("relay_uptime", 10, sim_relay_uptime)
    Timeout.new("t", 30, test_fill100_a)

def test_fill100_a(_):
    Log.info("driver: test_fill100_a")
    mqtt_client.publish(H2O_PREFIX + "CoarseLevelPct", "79.9")
    Timeout.new("t", 5, test_fill100_b)

def test_fill100_b(_):
    Log.info("driver: test_fill100_b")
    assert ctx['sm'] == "On"
    Timeout.new("t", 5, test_fill100_c)

def test_fill100_c(_):
    Log.info("driver: test_fill100_c")
    assert ctx['sm'] == "On"
    mqtt_client.publish(H2O_PREFIX + "CoarseLevelPct", "80.0")
    Timeout.new("t", 5, test_fill100_d)

def test_fill100_d(_):
    Log.info("driver: test_fill100_d")
    assert ctx['sm'] == "On"
    def stepper(task):
        mqtt_client.publish(H2O_PREFIX + "EstimatedLevelStr", "80% + 0L")
        mqtt_client.publish(H2O_PREFIX + "CoarseLevelPct", "80.0")
        if stepper.x >= 6:
            Timeout.new("t", 0, test_fill100_e)
        else:
            stepper.x += 1
            task.restart()
    stepper.x = 1
    Timeout.new("t", 10, stepper)

def test_fill100_e(_):
    Log.info("driver: test_fill100_e")
    assert ctx['sm'] == "On"
    mqtt_client.publish(H2O_PREFIX + "CoarseLevelPct", "80.0")
    Timeout.new("t", 5, test_fill100_rest)

def test_fill100_rest(_):
    Log.info("driver: test_rest_rest")
    assert ctx['sm'] == "Resting"
    Timeout.new("t", 5, stop)

def stop(_):
    Log.info("driver: stopping")
    ctx['h2o_uptime_task'].cancel()
    ctx['relay_uptime_task'].cancel()
    def stop(_):
        raise KeyboardInterrupt()
    Timeout.new("exit", 5, stop)

loop = EventLoop()
mqtt_client = start_mqtt()

# Test start
Timeout.new("t", 10, assert_offline)

try:
    loop.loop()
except Exception:
    mqtt_client.loop_stop()
    raise
