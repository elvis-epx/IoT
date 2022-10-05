#!/bin/bash

. unit/defs.sh

sensors 20 40 60 80 100
nvram_nowifi
runme
advance 45
cond state eq "Off"
cond pump eq 1
cond level_err eq 0
