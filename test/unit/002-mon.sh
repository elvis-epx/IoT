#!/bin/bash

. unit/defs.sh

sensors 20 40
runme
sleep 10
cond state eq "On"
cond pump eq 1
cond level_err eq 0

flow 10 5

sensors 20 40
mqtt mon-up
sleep 3
cond state eq "On MQTT"
cond pump eq 1

sensors 20 40 
mqtt mon-down
sleep 3
cond state eq "On"
cond pump eq 1

sensors 20 40
mqtt mon-up
sleep 3
cond state eq "On MQTT"
cond pump eq 1

sensors 20 40
mqtt moff-up
sleep 3
cond state eq "Off MQTT"
cond pump eq 0

sensors 20 40
mqtt moff-down
mqtt mon-down
sleep 3
cond state eq "On"
cond pump eq 1

sensors 20 40 60 80 100
sleep 3
cond state eq "Resting"
cond pump eq 0
cond level_err eq 0
