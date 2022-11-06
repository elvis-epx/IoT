#!/bin/bash

. unit/defs.sh

sensors 20 40 60
nvram
runme
sleep 5
cond state eq "On"
cond pump eq 0
cond level_err eq 0

# Test detection of rate too low for short-term flow
# 4 minutes tolerance to fill pipe 
fastflow 1 300

cond state eq "F slow 2"
cond pump eq 1

sensors 20 40 60 80 100
sleep 5

advance $((2 * 3600))
cond state eq "Off"
cond pump eq 1
