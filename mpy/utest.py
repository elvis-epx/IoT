#!/usr/bin/env python3

import sys, os
os.chdir(sys.argv[1])

sys.path.insert(0, '.')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../lib')
sys.path.insert(0, '../../testmock')

import builtins
builtins.const = lambda x: x

import time
time.sleep_ms = lambda t: time.sleep(t / 1000)
time.ticks_ms = lambda: int(time.time() * 1000)
time.ticks_us = lambda: int(time.time() * 1000000)
time.ticks_add = lambda a, b: a + b
time.ticks_diff = lambda a, b: a - b

import gc
gc.mem_alloc = lambda: 12345
gc.mem_free = lambda: 54321

if len(sys.argv) < 2:
    raise Exception("Test folder should be passed")

print("Importing unittest")
import importlib
main = importlib.import_module('unittest_meat')
print("Finished unittest")
