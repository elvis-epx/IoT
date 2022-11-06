#!/bin/bash

. unit/defs.sh

sensors 20 40 60
nvram
runme
sleep 10
cond state eq "On"
cond pump eq 0
cond level_err eq 0

# Test detection of rate too low for long-term flow
# 4 minutes tolerance to fill pipe 
# Short-term flow fail: <25% of expected flow
# Long-term flow fail: <33% of expected flow
# To simulate fail, must be between one and other

# Simulate 4.3L/min (between 3.6 and 4.83)
fastflow 21 $((31 * 60))

cond state eq "F slow 30"
cond pump eq 1

sensors 20 40 60 80 100

# Recovery time
sleep 5
advance $((12 * 3600))
cond state eq "Off"
cond pump eq 1
