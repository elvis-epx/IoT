#!/usr/bin/env python3

import sys


class OOKParser:
    # Generic ASK/OOK parser for 433MHz keyfobs
    # Assumption: every bit is composed of two level transitions

    name = ""
    # bitseq LH = bit is formed by a transition to low, then a transition to high
    #             and first transition is a delimiter
    #             Chirp examples: 001=1, 011=0
    # bitseq HL = bit is formed by a transition to high, then a transition to low
    #             and last transition is a delimiter
    #             Chirp examples: 1110=1, 1000=0
    bitseq = "LH"

    # bit1 LS = bit 1 is formed by a long-timed level followed by a short-timed level
    #           (and bit 0 is the opposite)
    #           Chirp examples: 1110=1 and 1000=0, or 001=1 and 011=0
    # bit1 SL = bit 1 is formed by a short-timed level followed by a long-timed level
    #           Chirp examples: 1110=0 and 1000=1, or 001=0 and 011=1
    bit1 = "LS" 

    def __init__(self, sequence):
        self.sequence = sequence[:]
        self.code = 0

    def res(self):
        return "%s:%d" % (self.name, self.code)

    # Parsing routine
    def parse(self):
        if len(self.sequence) != self.exp_sequence_len:
            return False

        lh = (self.bitseq == "LH") and 1 or 0
        ls = (self.bitseq == "LS") and 1 or 0
        bitcount = len(self.sequence) // 2
        self.code = 0

        for i in range(0, bitcount):
            lsbit = (self.sequence[i*2+lh][1] > self.sequence[i*2+1+lh][1]) and 1 or 0
            self.code = (self.code << 1) | (lsbit ^ ls)

        return True


class HT6P20(OOKParser):
    name = "HT6P20"
    exp_sequence_len = 57
    bitseq = "LH" # low then high (011, 001)
    bit1 = "LS" # long then short (001)


class EV1527(OOKParser):
    name = "EV1527"
    exp_sequence_len = 49
    bitseq = "HL" # high then low (1000 and 1110)
    bit1 = "LS" # long then short (1110)

parsers = [EV1527, HT6P20]

def parse(sequence):
    for parser_class in parsers:
        parser = parser_class(sequence)
        if parser.parse():
            print(parser.res())
            break
    else:
        print("Failed to parse")


for row in open(sys.argv[1]).readlines():
    row = row.strip()
    if not row:
        continue
    row = eval(row)
    print("----------------")
    print(row)
    parse(row)
