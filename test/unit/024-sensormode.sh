#!/bin/bash

. unit/defs.sh

sensors 20 40 60 80 100
nvram_sensormode
runme
advance 45
cond state eq "Sensor"
cond level_err eq 0
