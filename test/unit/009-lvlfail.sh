#!/bin/bash

. unit/defs.sh

sensors 20 40 60
runme
sleep 10
cond state eq "On"
cond pump eq 1
cond level_err eq 0

# Test detection of level unchanged in spite of good flow
# 100 pulses/s (~20L/min) x >20 min
fastflow 100 1400

cond state eq "F level"
cond pump eq 0

advance $((3600 * 6))

sensors 20 40 60 80 100
cond state eq "F level"
cond pump eq 0

advance $((3600 * 6))
sleep 5

cond state eq "Off"
cond pump eq 0
