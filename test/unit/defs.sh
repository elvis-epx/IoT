#!/bin/bash

set -e
rm -f *.sim

function sensors () {
    ./sensors $*
}

function mqtt () {
    ./mqtt $*
    sleep 1
}

function cond () {
    ./cond $1 $2 "$3"
}

# Simulate pulses of flow meter: $1 pulses/sec for $2 seconds
function flow () {
    rounds=$2
    while [ "$rounds" -gt 0 ]; do
        echo $1 > pulses.sim
        sleep 1
        rounds=$(($rounds - 1))
    done
}

# Simulate time passing of $1 seconds
function advance () {
    echo $1 > timeadvance.sim
    while [ -e timeadvance.sim ]; do
        sleep 0.1
    done
}

# Simulate pulses of flow meter and accelerate time passing
# $1 pulses/sec for $2 seconds

function fastflow () {
    # Advance $pitch s per cycle, as fast as program under test can take it
    pitch=10
    pulses=$(($1 * $pitch))
    rounds=$(($2 / $pitch))
    while [ "$rounds" -gt 0 ]; do
        echo $pulses > pulses.sim
        echo $pitch > timeadvance.sim
        while [ -e timeadvance.sim ] || [ -e pulses.sim ]; do
            sleep 0.1
        done
        rounds=$(($rounds - 1))
    done
}

function runme () {
    if which valgrind >/dev/null; then
        ./val &
    else
        ./test &
    fi
    export err=0
    export PID=$!
    sleep 5
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

function nvram () {
    echo "ssid" > nvram.sim
    if [ "$(($RANDOM % 2))" = 0 ]; then
        echo "foo" >> nvram.sim
    else
        echo "None" >> nvram.sim
    fi
    echo "password" >> nvram.sim
    if [ "$(($RANDOM % 2))" = 0 ]; then
        echo "None" >> nvram.sim
    else
        echo "bar" >> nvram.sim
    fi
    echo "mqtt" >> nvram.sim
    if [ "$(($RANDOM % 2))" = 0 ]; then
        echo "1.2.3.4" >> nvram.sim
    else
        echo "None" >> nvram.sim
    fi
    echo "mqttport" >> nvram.sim
    if [ "$(($RANDOM % 2))" = 0 ]; then
        echo "None" >> nvram.sim
    else
        echo "1883" >> nvram.sim
    fi
}

function cli () {
    echo $* >> serial.sim
}

trap quit EXIT
