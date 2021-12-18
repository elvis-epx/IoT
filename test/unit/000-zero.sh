#!/bin/bash

. unit/defs.sh

sensors 20 40 60 80 100
runme
cond state eq "Off"
cond pump eq 0
