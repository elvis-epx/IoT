#!/bin/bash

. unit/defs.sh

sensors 20 40 60
runme
sleep 10
cond state eq "On"
cond pump eq 1
cond level_err eq 0

flow 10 10

sensors 20 40 60 80 100
sleep 5
cond state eq "Resting"
cond pump eq 0

sleep 310

cond state eq "Off"
cond pump eq 0
