#!/bin/bash

. unit/defs.sh

sensors 20 40 60
runme
sleep 10
cond state eq "On"
cond pump eq 0
cond level_err eq 0
cond level% eq 60

# 1100 / 60 = 18.33L/min expected flow
# 25mm x 75m ~= 36L pipe capacity between pump and sensor
# expected time to fill pipes: ~2min

sleep 120
cond state eq "On"

# Fail after 2x expected time

sleep 120
cond state eq "F flow"
cond pump eq 1
