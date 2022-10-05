#!/bin/bash

. unit/defs.sh

sensors 20 40 60
nvram_invmqtt
runme
sleep 10
cond state eq "On"
cond pump eq 0
cond level_err eq 0
cond level% eq 60

advance 160
sleep 2
cond state eq "On"

# Fail after 2x expected time

advance 160
sleep 2
cond state eq "F flow"
cond pump eq 1
