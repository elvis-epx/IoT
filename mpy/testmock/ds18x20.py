import time
import sys
import os, os.path
import statistics as s
from epx import loop

class DS18X20:
    def __init__(self, onewire):
        self.onewire = onewire
        self.temps = {b'0001': 85.0, b'0002': 85.0, b'0003': 85.0}

    def scan(self):
        # TODO simulate empty
        return self.temps.keys()

    def convert_temp(self):
        # TODO simulate noise, abrupt change, etc.
        # TODO simulte exception
        self.temps[b'0001'] = 21.0
        self.temps[b'0002'] = 22.0
        self.temps[b'0003'] = 23.0

    def read_temp(self, rom):
        # TODO simulate exception
        n = s.NormalDist(mu=self.temps[rom], sigma=0.1)
        return n.samples(1)[0]
