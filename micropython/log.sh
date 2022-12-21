#!/bin/bash -x

pyboard.py -d /dev/ttyUSB0 | tee -a log
