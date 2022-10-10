#!/usr/bin/env python3

import json, time, random

def read_state():
    l = []
    while len(l) < 7: 
        try:
            l = open("state.sim").readlines()
        except FileNotFoundError:
            pass
        if len(l) < 7:
            print("Waiting for state.sim...")
            time.sleep(1)

    d = {}
    d["state"] = l[0].strip()
    d["level%"] = float(l[1].strip())
    d["levelL"] = float(l[2].strip())
    d["rate0"] = float(l[3].strip())
    d["rate1"] = float(l[4].strip())
    d["rate2"] = float(l[5].strip())
    d["level_err"] = ("E" in l[6]) and 1 or 0

    l = []
    while len(l) < 1:
        try:
            l = open("gpiomcpw.sim").readlines()
        except FileNotFoundError:
            pass
        if len(l) < 1:
            print("Waiting for gpiomcpw.sim...")
            time.sleep(1)

    d["pump"] = float(l[0])
    return d

def gen_sensors(items):
    args = {}
    args["20"] = 1
    args["40"] = 2
    args["60"] = 4
    args["80"] = 8
    args["100"] = 16
    
    bitmap = 255
    for arg in items[1:]:
        bitmap = bitmap & ~args[arg]
    
    open("gpiomcpr.sim", "w").write("%d" % bitmap)

def gen_mqtt(item):
    args = {}
    on = random.choice(["On", "on", "1"])
    off = random.choice(["Off", "off", "0"])
    inval = random.choice(["", "o", "O", "of", "Invalid"])
    args["mon-up"] = ("cmnd/H2OControl/OverrideOn", on)
    args["mon-down"] = ("cmnd/H2OControl/OverrideOn", off)
    args["moff-up"] = ("cmnd/H2OControl/OverrideOff", on)
    args["moff-down"] = ("cmnd/H2OControl/OverrideOff", off)
    args["inval-sub"] = ("cmnd/H2OControl/Invalid", off)
    args["inval-mon"] = ("cmnd/H2OControl/OverrideOn", inval)
    args["inval-moff"] = ("cmnd/H2OControl/OverrideOff", inval)
    
    open("mqtt.sim", "w").write("%s\n%s\nOk\n" % args[item])

def gen_mqtt_ota(password):
    open("mqtt.sim", "w").write("cmnd/H2OControl/OTA\n%s\nOk\n" % password)
