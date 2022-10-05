#!/bin/bash

. unit/defs.sh

sensors 20 40 60 80 100
nvram
runme
cond state eq "Off"
cond pump eq 1
advance 45

echo "Invalid MQTT messages"
mqtt inval-mon
sleep 2
cond state eq "Off"
mqtt inval-moff
sleep 2
cond state eq "Off"
mqtt inval-sub
sleep 2
cond state eq "Off"

cond level_err eq 0
