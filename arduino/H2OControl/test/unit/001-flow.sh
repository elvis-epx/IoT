#!/bin/bash

. unit/defs.sh

sensors 20 40 60 80
nvram_nowifi
runme
advance 45
cond level% eq 80
cond levelL eq 800

fastflow 30 120
cond levelplus eq 12.5
cond rate gt 6.1
cond rate lt 6.4

fastflow 1 120
cond levelplus gt 12.9
cond levelplus lt 13.0
cond rate gt 0.205
cond rate lt 0.215

fastflow 0 120
cond levelplus gt 12.9
cond levelplus lt 13.0
cond rate eq 0
