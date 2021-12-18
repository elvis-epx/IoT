#!/usr/bin/env python3

import json, sys, mylib

out = mylib.gen_constant_h(open(sys.argv[1]).read())
open("Constants.h", "w").write(out)
