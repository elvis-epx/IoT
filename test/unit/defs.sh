#!/bin/bash

set -e
rm -f *.sim

function sensors () {
	./sensors $*
}

function cond () {
	./cond $*
}

function runme () {
	./val &
	export err=0
	export PID=$!
}

function quit () {
	err=$?
	echo > quit.sim
	if ! wait $PID; then
		echo "test.cpp exited with error"
		exit 1
	fi
	exit $err
}

trap quit EXIT
