#!/usr/bin/env python3

import sys, os
os.chdir(sys.argv[2])
sys.path.insert(0, '../../')
sys.path.insert(0, '../../lib')
sys.path.insert(0, '../../testmock')

flavor = sys.argv[1]

import builtins
builtins.const = lambda x: x

import time
time.sleep_ms = lambda t: time.sleep(t / 1000)
time.ticks_ms = lambda: int(time.time() * 1000)
time.ticks_add = lambda a, b: a + b
time.ticks_diff = lambda a, b: a - b

import gc
gc.mem_alloc = lambda: 12345
gc.mem_free = lambda: 54321

import machine
if len(sys.argv) < 3:
    raise Exception("Flavor and test folder should be passed")

import importlib

boot = importlib.import_module(flavor + '_boot')
stage = importlib.import_module(flavor + '_stage')
while machine.test_mock(None):
    pass
main = importlib.import_module(flavor + '_main')
