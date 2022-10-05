#!/bin/bash

. unit/defs.sh

sensors 20 40 60 80 100
nvram
runme
cond state eq "Off"
cond pump eq 1
advance 45

echo "Manual off override"
sensors 20 40 60 80 100
mqtt moff-up
sleep 2
cond state eq "Off MQTT"
cond pump eq 1

cond level_err eq 0
