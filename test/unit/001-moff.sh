#!/bin/bash

. unit/defs.sh

sensors 20 40 60 80 100
runme
cond state eq "Off"
cond pump eq 0

echo "Manual off override"
sensors 20 40 60 80 100 moff
sleep 2
cond state eq "Off MQTT"
cond pump eq 0

cond level_err eq 0
