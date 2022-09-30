#!/bin/bash

. unit/defs.sh

sensors 20 40
runme
sleep 5

echo "Block 1"
cond state eq "On"
cond pump eq 0
cond level_err eq 0

flow 10 5

echo "Block 2"
sensors 20 40
mqtt mon-up
sleep 2
cond state eq "On MQTT"
cond pump eq 0

echo "Block 3"
sensors 20 40 
mqtt mon-down
sleep 2
cond state eq "On"
cond pump eq 0

echo "Block 4"
sensors 20 40
mqtt mon-up
sleep 2
cond state eq "On MQTT"
cond pump eq 0

echo "Block 5"
sensors 20 40
mqtt moff-up
sleep 2
cond state eq "Off MQTT"
cond pump eq 1

echo "Block 6"
sensors 20 40
mqtt moff-down
mqtt mon-down
sleep 2
cond state eq "On"
cond pump eq 0

echo "Block 7"
sensors 20 40 60 80 100
sleep 3
cond state eq "Resting"
cond pump eq 1
cond level_err eq 0

echo "Block 8"
mqtt mon-up
sleep 4
cond state eq "On MQTT"
mqtt mon-down
sleep 2
cond state eq "Off"
mqtt moff-up
sleep 2
cond state eq "Off MQTT"
mqtt moff-down
sleep 2
cond state eq "Off"
