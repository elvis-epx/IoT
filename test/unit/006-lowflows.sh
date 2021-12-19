#!/bin/bash

. unit/defs.sh

sensors 20 40 60
runme
sleep 10
cond state eq "On"
cond pump eq 1
cond level_err eq 0

# Test detection of rate too low for short-term flow
# 4 minutes tolerance to fill pipe 
flow 1 300

cond state eq "Fail low flow S"
cond pump eq 0
