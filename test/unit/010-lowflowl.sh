#!/bin/bash

. unit/defs.sh

sensors 20 40 60
runme
sleep 10
cond state eq "On"
cond pump eq 1
cond level_err eq 0

# Test detection of rate too low for long-term flow
# 4 minutes tolerance to fill pipe 
# Short-term flow fail: <25% of expected flow
# Long-term flow fail: <33% of expected flow
# To simulate fail, must be between one and other

# Simulate 5.6L/min (between 4.6 and 6.1)
fastflow 27 $((31 * 60))

cond state eq "F flow 30"
cond pump eq 0

sensors 20 40 60 80 100

# Recovery time
advance $((12 * 3600))
sleep 5
cond state eq "Off"
cond pump eq 0
