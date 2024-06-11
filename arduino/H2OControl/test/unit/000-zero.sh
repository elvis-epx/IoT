#!/bin/bash

. unit/defs.sh

sensors 20 40 60 80
nvram_nowifi
runme
advance 45
cond level_err eq 0
cond level% eq 80
cond levelL eq 800
