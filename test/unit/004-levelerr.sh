#!/bin/bash

. unit/defs.sh

sensors 20 60 80
runme
cond state eq "Off"
cond pump eq 1
cond level% eq 80
cond level_err eq 1
