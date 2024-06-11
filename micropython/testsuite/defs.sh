#!/bin/bash

if [ "$TEST_FOLDER" = "" ]; then
        echo "TEST_FOLDER must be defined"
        exit 1
fi

if [ "$FLAVOR" = "" ]; then
        echo "FLAVOR must be defined"
        exit 1
fi

set -e
rm -rf ${TEST_FOLDER}/*.sim

function mqttsub () {
    echo -e "$1\n$2\n$3\n$4" > ${TEST_FOLDER}/mqttsub.sim
    while [ -e ${TEST_FOLDER}/mqttsub.sim ]; do
        sleep 1
    done
}

# Simulate time passing of $1 milisseconds
function advance () {
    echo $1 > ${TEST_FOLDER}/advance.sim
    while [ -e ${TEST_FOLDER}/advance.sim ]; do
        sleep 1
    done
}

# Simulate WiFi status
function wifi () {
    echo $1 > ${TEST_FOLDER}/wifi.sim
    while [ -e ${TEST_FOLDER}/wifi.sim ]; do
        sleep 1
    done
}

# Simulate MQTT failure modes
function mqttfail () {
    echo $1 > ${TEST_FOLDER}/mqttfail.sim
    while [ -e ${TEST_FOLDER}/mqttfail.sim ]; do
        sleep 1
    done
}

function bme280 () {
    echo $1 > ${TEST_FOLDER}/bme280.sim
    while [ -e ${TEST_FOLDER}/bme280.sim ]; do
        sleep 1
    done
}

function bme280f () {
    echo $1 > ${TEST_FOLDER}/bme280f.sim
}

function ssd1306f () {
    echo $1 > ${TEST_FOLDER}/ssd1306f.sim
}

function mcp23017f () {
    echo fail > ${TEST_FOLDER}/mcp23017.sim
}

function mcp23017nf () {
    echo good > ${TEST_FOLDER}/mcp23017.sim
}

function pzemf () {
    echo $1 > ${TEST_FOLDER}/pzem.sim
}

function pulse () {
    echo $2 > ${TEST_FOLDER}/pulse$1.sim
    while [ -e ${TEST_FOLDER}/pulse$1.sim ]; do
        sleep 0.1
    done
}

function mcp23017 () {
    echo $1 > ${TEST_FOLDER}/mcp23017.sim
    while [ -e ${TEST_FOLDER}/mcp23017.sim ]; do
        sleep 1
    done
}

function hdc1080 () {
    echo $1 > ${TEST_FOLDER}/hdc1080.sim
    while [ -e ${TEST_FOLDER}/hdc1080.sim ]; do
        sleep 1
    done
}

function hdc1080f () {
    echo $1 > ${TEST_FOLDER}/hdc1080f.sim
}

function mqttblock () {
    echo $1 > ${TEST_FOLDER}/mqttblock.sim
    while [ -e ${TEST_FOLDER}/mqttblock.sim ]; do
        sleep 1
    done
}

function wdtblock () {
    echo $1 > ${TEST_FOLDER}/wdtblock.sim
    while [ -e ${TEST_FOLDER}/wdtblock.sim ]; do
        sleep 1
    done
}

function assert_gpio () 
{
    f=${TEST_FOLDER}/pin${1}.sim
    while ! [ -f $f ]; do
        echo "waiting for $f..."
        sleep 1
    done
    g=`cat $f`
    if [ "$g" = "$2" ]; then
        return 0
    fi
    echo "GPIO pin $1 got unexpected value"
    return 1
}

function assert_mqtt ()
{
    f=${TEST_FOLDER}/mqttpub.sim
    while ! [ -f $f ]; do
        echo "waiting for $f..."
        sleep 1
    done
    while ! grep "$1" ${TEST_FOLDER}/mqttpub.sim >/dev/null; do
        echo "waiting for $1 in $f..."
        sleep 1
    done
    LASTPUB=`grep "$1" ${TEST_FOLDER}/mqttpub.sim | tail -1`
    if echo "$LASTPUB" | grep " $2" >/dev/null; then
        return 0
    fi
    echo "MQTT topic $1 got unexpected msg, expected $2"
    echo "Received: $LASTPUB"
    return 1
}

function assert () {
    if [ "$1" = "gpio" ]; then
        assert_gpio "$2" "$3"
    elif [ "$1" = "mqtt" ]; then
        assert_mqtt "$2" "$3"
    else
        echo "Unsupported assert"
        return 1
    fi
}

function gpio () {
    echo "$2" > ${TEST_FOLDER}/pin${1}.sim
}

# Usage: i|b namespace key value
function nvram () {
    echo -n "$4" > ${TEST_FOLDER}/nvram_${1}_${2}_${3}.sim
    if [ "$1" = "b" ]; then
        echo -n "${#4}" > ${TEST_FOLDER}/nvram_i_${2}_${3}_len.sim
    fi
}

function runme () {
    python3-coverage run test.py $FLAVOR $TEST_FOLDER &
    export err=0
    export PID=$!
    sleep 5
}

function quit () {
    touch ${TEST_FOLDER}/quit.sim
}

function has_quit () {
    if ps -p $PID >/dev/null; then
        return 1
    else
        return 0
    fi
}

function quit_trap ()
{
    err=$?
    if ! has_quit; then
        echo "trap script exit"
        quit
        if ! wait $PID; then
            echo "exited with error"
            exit 1
        fi
    fi
    trap '' EXIT
    exit $err
}

trap quit_trap EXIT
