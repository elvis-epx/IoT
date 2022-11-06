#!/bin/bash

. unit/defs.sh

sensors 20 40 60
runme
sleep 10
cond level% eq 60
sensors 20 40 60 80
sleep 2
cond level% eq 60
sleep 5
cond level% eq 80
