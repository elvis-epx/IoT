#!/usr/bin/env python3

import json, time, random

def read_state():
    l = []
    while len(l) < 4: 
        try:
            l = open("state.sim").readlines()
        except FileNotFoundError:
            pass
        if len(l) < 4:
            print("Waiting for state.sim...")
            time.sleep(1)

    d = {}
    d["level%"] = float(l[0].strip())
    d["levelL"] = float(l[1].strip())
    d["levelplus"] = float(l[2].strip())
    d["rate"] = float(l[3].strip())
    d["level_err"] = ("E" in l[4]) and 1 or 0

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
    args["inval-sub"] = ("cmnd/H2OControl/Invalid", off)
    
    open("mqtt.sim", "w").write("%s\n%s\nOk\n" % args[item])

def gen_mqtt_ota(password):
    open("mqtt.sim", "w").write("cmnd/H2OControl/OTA\n%s\nOk\n" % password)
