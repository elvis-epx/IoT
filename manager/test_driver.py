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
    Timeout.new("t", 30, assert_online)

def assert_online(_):
    Log.info("driver: assert_online")
    assert ctx['sm'] == "Off"
    mqtt_client.publish(H2O_PREFIX + "EstimatedLevelStr", "60% + 0L")
    Timeout.new("t", 5, test_startup_a)

def test_startup_a(_):
    Log.info("driver: test_statup_a")
    mqtt_client.publish(H2O_PREFIX + "CoarseLevelPct", "79.7")
    Timeout.new("t", 5, test_startup_b)

def test_startup_b(_):
    Log.info("driver: test_statup_b")
    assert ctx['sm'] == "On"
    Timeout.new("t", 65, test_lowflow_1)

# Test total absence of flow
def test_lowflow_1(_):
    Log.info("driver: test_lowflow_1")
    assert ctx['sm'] == "LowFlowError"
    Timeout.new("t", 125, test_lowflow_recover)

def test_lowflow_recover(_):
    Log.info("driver: test_lowflow_recover")
    assert ctx['sm'] == "Off"
    Timeout.new("t", 0, test_startup_c)

def test_startup_c(_):
    Log.info("driver: test_statup_c")
    mqtt_client.publish(H2O_PREFIX + "CoarseLevelPct", "79.7")
    Timeout.new("t", 5, test_fillup_a)

def test_fillup_a(_):
    Log.info("driver: test_fillup_a")
    assert ctx['sm'] == "On"
    mqtt_client.publish(H2O_PREFIX + "EstimatedLevelStr", "80% + 10L")
    mqtt_client.publish(H2O_PREFIX + "Flow", "10.0")
    Timeout.new("t", 5, test_fillup_b)

def test_fillup_b(_):
    Log.info("driver: test_fillup_b")
    assert ctx['sm'] == "On"
    mqtt_client.publish(H2O_PREFIX + "CoarseLevelPct", "99.99999")
    Timeout.new("t", 5, test_rest)

def test_rest(_):
    Log.info("driver: test_rest_a")
    assert ctx['sm'] == "Resting"
    Timeout.new("t", 35, test_rest_end)

def test_rest_end(_):
    Log.info("driver: test_rest_end")
    assert ctx['sm'] == "Off"
    Timeout.new("t", 0, test_timeout_a)

def test_timeout_a(_):
    Log.info("driver: test_timeout_a")
    mqtt_client.publish(H2O_PREFIX + "CoarseLevelPct", "79.7")
    Timeout.new("t", 5, test_timeout_b)

def test_timeout_b(_):
    Log.info("driver: test_timeout_b")
    assert ctx['sm'] == "On"

    # simulate flow but never fill up, until TimeoutErro
    def sim_flow(task):
        mqtt_client.publish(H2O_PREFIX + "Flow", "10.0")
        mqtt_client.publish(H2O_PREFIX + "CoarseLevelPct", "79.7")
        mqtt_client.publish(H2O_PREFIX + "EstimatedLevelStr", "80% + 10L")
        if ctx['sm'] == 'TimeoutError':
            Timeout.new("t", 125, test_timeout_recover)
            return
        task.restart()
    Timeout.new("t", 5, sim_flow)

def test_timeout_recover(_):
    Log.info("driver: test_timeout_recover")
    assert ctx['sm'] == "Off"

    mqtt_client.publish(H2O_CPREFIX + "ManualOn", "1")
    Timeout.new("t", 3, test_manualon)

def test_manualon(_):
    Log.info("driver: test_manualon")
    assert ctx['sm'] == "ManualOn"

    mqtt_client.publish(H2O_CPREFIX + "ManualOn", "1")
    Timeout.new("t", 3, test_manualon2)
    
def test_manualon2(_):
    Log.info("driver: test_manualon2")
    assert ctx['sm'] == "ManualOn"

    mqtt_client.publish(H2O_CPREFIX + "ManualOn", "0")
    Timeout.new("t", 3, test_manualon_down)
    
def test_manualon_down(_):
    Log.info("driver: test_manualon_down")
    assert ctx['sm'] == "Resting"

    mqtt_client.publish(H2O_CPREFIX + "ManualOff", "1")
    Timeout.new("t", 3, test_manualoff)
    
def test_manualoff(_):
    Log.info("driver: test_manualoff")
    assert ctx['sm'] == "ManualOff"

    mqtt_client.publish(H2O_CPREFIX + "ManualOff", "0")
    Timeout.new("t", 3, test_manualoff2)

def test_manualoff2(_):
    Log.info("driver: test_manualoff2")
    assert ctx['sm'] == "Off"

    mqtt_client.publish(H2O_PREFIX + "Malfunction", "2")
    Timeout.new("t", 3, test_malfunction)

def test_malfunction(_):
    Log.info("driver: test_malfunction")
    assert ctx['sm'] == "Malfunction"

    mqtt_client.publish(H2O_PREFIX + "Malfunction", "0")
    Timeout.new("t", 3, test_malfunction_cl)

def test_malfunction_cl(_):
    Log.info("driver: test_malfunction_cl")
    assert ctx['sm'] == "Off"

    Timeout.new("t", 0, go_offline)

def go_offline(_):
    Log.info("driver: go_offline")
    ctx['h2o_uptime_task'].cancel()
    ctx['relay_uptime_task'].cancel()
    Timeout.new("t", 180, assert_offline_final)

def assert_offline_final(_):
    Log.info("driver: assert_offline_final")
    assert ctx['sm'] == "Offline"
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
