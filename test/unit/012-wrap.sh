#!/bin/bash

. unit/defs.sh

sensors 20 40 60 80 100
runme
cond state eq "Off"

echo "Advancing 1M seconds"
advance 1000000
sleep 5
echo "Advancing 1M seconds"
advance 1000000
sleep 5
echo "Advancing 1M seconds"
advance 1000000
sleep 5
echo "Advancing 1M seconds"
advance 1000000
sleep 5
# Provoke wrap-around of millis()
echo "Advancing 500k seconds"
advance 500000
# Check the uptime is >46 days
sleep 5
