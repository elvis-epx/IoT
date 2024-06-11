#!/bin/bash

. unit/defs.sh

sensors 20 40 60 80 100
nvram
runme
advance 45

echo "Invalid MQTT messages"
mqtt inval-sub
sleep 2
cond level_err eq 0
