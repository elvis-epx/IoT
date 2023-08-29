#!/bin/bash -x

pyboard.py -d /dev/$(cat serial.txt) | tee -a log
