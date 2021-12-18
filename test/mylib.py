#!/usr/bin/env python3

import json

def gen_constant_h(jsondata):
	constants = json.loads(jsondata)

	out = """#ifndef __CONSTANTS_H
#define __CONSTANTS_H

#define TANK_CAPACITY %.1f // liters""" % constants["capacity"]

	out += """
// ought to be just below the second sensor, top to bottom
#define LOWLEVEL_THRESHOLD %.1f // %%
""" % constants["lowlevel_threshold"]

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
