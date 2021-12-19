#!/bin/bash

. unit/defs.sh

sensors 20 40
runme
sleep 10
cond state eq "On"
cond pump eq 1
cond level_err eq 0

sensors 20 40 mon
sleep 3
cond state eq "On (manual)"
cond pump eq 1

sensors 20 40 mon moff
sleep 3
cond state eq "Off (manual)"
cond pump eq 0

sensors 20 40
sleep 3
cond state eq "On"
cond pump eq 1

sensors 20 40 60 80 100
sleep 3
cond state eq "Off, rest"
cond pump eq 0
cond level_err eq 0
