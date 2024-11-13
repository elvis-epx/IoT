#!/usr/bin/env python3

import sys

class OOKEncoder:
    # Generic ASK/OOK generator for 433MHz protocols
    chirp_time = 500 # µs
    chirps = ("011", "001") # 0 and 1 respectively
    preamble1 = "1000000000" # normally starts with 1 to ping/calibrate rx
    preamble2 = "1" # low-then-high codes should have a "1" at the end of preamble
    trailer = "" # high-then-low codes should have an "1" trailer
    code_bits = 24  # number of bits spanned by the code word

    def __init__(self):
        pass

    def encode(self, code):
        # Convert bits to chirps
        chirp_seq_pre = "0" + self.preamble1
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

        # Convert chirps to level transitions
        current_level = -1
        levels = []
        for chirp in chirp_seq:
            if chirp != current_level:
                levels.append([chirp, self.chirp_time])
                current_level = chirp
                continue
            levels[-1][1] += self.chirp_time

        return rmtwaveform, levels


class HT6P20(OOKEncoder):
    name = "HT6P20"
    chirp_time = 500 # µs
    chirps = ("011", "001")
    preamble1 = "1" + ("0" * 23) 
    preamble2 = "1"
    trailer = ""
    code_bits = 28 # code must supply the suffix 0b0101


class EV1527(OOKEncoder):
    name = "EV1527"
    chirp_time = 333 # µs
    chirps = ("1000", "1110")
    preamble = "1" + ("0" * 31)
    preamble2 = ""
    trailer = "1"
    code_bits = 24


encoders = {"EV1527": EV1527, "HT6P20": HT6P20}

encoder_class = encoders[sys.argv[1].upper()]
code = int(sys.argv[2])

rmt, trans = encoder_class().encode(code)
# "trans" is a list that can be printed to a file and decoded by test3.py
# "rmt" is a list ready to use in esp32.RMT
print(trans)
# print(rmt)
