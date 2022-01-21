#!/bin/bash

. unit/defs.sh

sensors
runme
sleep 10
cond state eq "On"
cond pump eq 0
cond level_err eq 0

# Test pump timeout (twice the complete fillup time at expected flow rate)
# 1000L / 18.33L/min = 54 min
# Pump timeout = 108min

# Simulate 10L/min to avoid stopping due to low flow
fastflow 48 $((30 * 60))
# Change level to avoid "level unchanged" failure
sensors 20
# -------------------------- 63 min mark

# More 30 min / 300L
fastflow 48 $((30 * 60))
# Change level 
sensors 20 40
# -------------------------- 60 min mark

# More 30 min / 300L
fastflow 48 $((30 * 60))
# Change level 
sensors 20 40 60
# -------------------------- 90 min mark

# More 20 min
fastflow 48 $((20 * 60))
# ------------- 110 min mark, > 108 min, should have fialed

cond state eq "F timeout"
cond pump eq 1

sensors 20 40 60 80 100

# Recovery time
advance $((6 * 3600))
sleep 5
cond state eq "Off"
cond pump eq 1
