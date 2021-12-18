#!/bin/bash

err=0
./sensors 20 40 60 80 100
./val &
PID=$!

sleep 5

./cond state eq "Off" || err=1
./cond pump eq 0 || err=1

echo > quit.sim
sleep 1

if ! wait $PID; then
	echo "test exited with error"
	err=1
fi

exit $err
