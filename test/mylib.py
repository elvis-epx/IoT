#!/usr/bin/env python3

import json, time

def gen_constant_h(jsondata):
	constants = json.loads(jsondata)

	out = """#ifndef __CONSTANTS_H
#define __CONSTANTS_H

#define TANK_CAPACITY %.1f // liters""" % constants["capacity"]

	out += """
// ought to be the second sensor, top to bottom
#define PUMP_THRESHOLD %.1f // %%
""" % constants["pump_threshold"]

	out += "#define LEVEL_SENSORS {"
	for level in constants["level_sensors"]:
		out += "%.1f, " % level
	out += """0.0}

"""

	out += """#define FLOWMETER_PULSE_RATE %.1f // in pulses/s when flow is 1L/min
#define ESTIMATED_PUMP_FLOWRATE (%.1f / 60) // in L/min

""" % (constants["flowmeter_pulse_rate"], constants["estimated_flowrate_h"])

	out += """// pipes between pump and flow meter
#define PIPE_DIAMETER %.1f // in mm
#define PIPE_LENGTH   %.1f // in m

""" % (constants["pipe_diameter"], constants["pipe_length"])

	fr = []

	for ts in constants["flowrate_timespans"]:
		if (ts % 60) != 0:
			fr.append(ts)
			fr.append("SECONDS")
		else:
			fr.append(ts / 60)
			fr.append("MINUTES")

	out += """// time spans to measure average flow rate
#define FLOWRATE_INSTANT (%.0f * %s)
#define FLOWRATE_SHORT   (%.0f * %s)
#define FLOWRATE_LONG    (%.0f * %s)
""" % tuple(fr)

	out += """
#define FLOWRATES {FLOWRATE_INSTANT, FLOWRATE_SHORT, FLOWRATE_LONG}

#endif
"""
	return out

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
			l = open("gpio2.sim").readlines()
		except FileNotFoundError:
			pass
		if len(l) < 1:
			print("Waiting for gpio2.sim...")
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
	
	open("gpio.sim", "w").write("%d" % bitmap)

def gen_mqtt(item):
	args = {}
	args["mon-up"] = 1
	args["mon-down"] = 2
	args["moff-up"] = 3
	args["moff-down"] = 4
	
	open("mqtt.sim", "w").write("%d" % args[item])
