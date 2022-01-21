#!/bin/bash

. unit/defs.sh

sensors 20 40 60
runme
cond state eq "On"
cond pump eq 0

fastflow 100 60

sensors 20 40 60 80
sleep 5
cond state eq "On"

fastflow 100 660

sensors 20 40 60 80 100

sleep 5
cond state eq "Resting"
cond pump eq 1
