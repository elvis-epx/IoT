#!/usr/bin/env python3

import sys, time
from esp32 import RMT
from machine import Pin

class OOKEncoder:
    # Generic ASK/OOK generator for 433MHz protocols
    chirp_time = 500 # µs
    chirps = ("011", "001") # 0 and 1 respectively
    preamble0 = "1" # ping/calibrate tx
    preamble1 = "000000000" # preamble before and between packets
    preamble2 = "1" # low-then-high codes should have a "1" at the end of preamble
    trailer = "" # high-then-low codes should have an "1" trailer
    code_bits = 24  # number of bits spanned by the code word
    repeat = 3 # send the code "n" times to increase chance of reception

    def __init__(self):
        pass

    def encode(self, code):
        # Convert bits to chirps
        chirp_seq_pre = "0" + self.preamble0 + self.preamble1
        chirp_seq = self.preamble2
        for i in range(self.code_bits - 1, -1, -1):
            bit = (code & (1 << i)) and 1 or 0
            chirp_seq += self.chirps[bit]
        chirp_seq += self.trailer
        chirp_seq_pos = "0"

        # Convert chirps to RMT waveform
        rmtwaveform = []
        current_level = -1
        for chirp in chirp_seq_pre + chirp_seq + chirp_seq_pos:
            if chirp != current_level:
                rmtwaveform.append(self.chirp_time)
                current_level = chirp
                continue
            rmtwaveform[-1] += self.chirp_time

        return rmtwaveform


class HT6P20(OOKEncoder):
    name = "HT6P20"
    chirp_time = 500 # µs
    chirps = ("011", "001")
    preamble1 = "0" * 23
    preamble2 = "1"
    trailer = ""
    code_bits = 28 # code must supply the suffix 0b0101


class EV1527(OOKEncoder):
    name = "EV1527"
    chirp_time = 333 # µs
    chirps = ("1000", "1110")
    preamble1 = "0" * 31
    preamble2 = ""
    trailer = "1"
    code_bits = 24

pin = Pin(14)
# Resolution 80 MHz / 80 = 1 MHz = 1µs
rmt = RMT(0, pin=pin, clock_div=80, idle_level=0)
# encoder = HT6P20()
# code = 12345669
encoder = EV1527()
code = 1234567

while True:
    print("Sending", code)
    rmtwaveform = encoder.encode(code)
    print(rmtwaveform)
    rmt.write_pulses(tuple(rmtwaveform), 0)
    time.sleep(2)
    code += 1
