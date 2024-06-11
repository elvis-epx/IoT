#!/bin/bash

. unit/defs.sh

sensors 20 40 60
runme
sleep 10
cond level% eq 60
sensors 20 40 60 80
sleep 1
cond level% eq 60
sleep 1
cond level% eq 60
sleep 1
cond level% eq 60
sleep 2
cond level% eq 80
sensors 20 40 60 80 100
sleep 2
cond level% eq 80
sleep 3
cond level% eq 100
