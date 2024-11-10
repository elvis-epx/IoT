#!/usr/bin/env python3

import sys

class HT6P20:
    name = "HT6P20"

    def __init__(self, sequence):
        self.sequence = sequence[:]
        self._ok = False
        self.code = "-"

    def ok(self):
        return self._ok

    def res(self):
        return "%s %s" % (self.name, self.code)

    # Transitions that are not 0-1 or 1-0, possibly due to some delay in
    # interrupt handling
    def false_transition(self):
        for i in range(0, len(self.sequence) - 1):
            if self.sequence[i][0] == self.sequence[i+1][0]:
                return (i, i+1)
        return None

    # Calculate average timing of each bit
    def bit_timing(self):
        tot = totsq = 0
        bitcount = len(self.sequence) // 2
        for i in range(0, bitcount):
            bittime = self.sequence[i*2][1] + self.sequence[i*2+1][1]
            tot += bittime
            totsq += bittime * bittime
        mean = tot / bitcount
        return mean, (totsq / bitcount - mean * mean) ** 0.5

    # Find if timing of a single bit is off
    def anomalous_bit_timing(self, std, dev):
        bitcount = len(self.sequence) // 2
        for i in range(0, bitcount):
            bit_time = self.sequence[i*2][1] + self.sequence[i*2+1][1]
            if bit_time < (std - dev) or bit_time > (std + dev):
                return (i, bit_time)
        return None

    # Find whether the length of a chirp is off
    def anomalous_chirp(self, short, shortdev, long, longdev):
        for i in range(0, len(self.sequence)):
            chirplen = self.sequence[i][1]
            if (chirplen >= (short - shortdev) and chirplen <= (short + shortdev)) or \
               (chirplen >= (long  - longdev)  and chirplen <= (long  + longdev)):
                pass
            else:
                return (i, chirplen)
        return None

    def do_parse(self):
        code = 0
        bitcount = len(self.sequence) // 2
        for i in range(0, bitcount):
            code <<= 1
            if self.sequence[i*2][1] > self.sequence[i*2+1][1]:
                # 1110 = bit 1
                code |= 1
        return code

    def run(self):
        false_trans = self.false_transition()
        if false_trans:
            print("> false trans %d-%d" % false_trans)
            return
        if len(self.sequence) != 57:
            print("> unexpected len")
            return
        if self.sequence[0][0] != 1:
            print("> unexpected first chirp")
            return
        self.sequence = self.sequence[1:57]
        bit_time, bit_time_dev = self.bit_timing()
        print("> bit timing %dus stddev %dus" % (bit_time, bit_time_dev))
        anom = self.anomalous_bit_timing(bit_time, bit_time * 0.25)
        if anom:
            print("> bit timing anomaly %d timing %d" % anom)
            return
        anom = self.anomalous_chirp(bit_time * 0.33, bit_time * 0.33 * 0.25,
                                    bit_time * 0.66, bit_time * 0.33 * 0.25)
        if anom:
            print("> chirp timing anomaly %d timing %d" % anom)
            return
        code = self.do_parse()
        self.code = "%d" % code
        self._ok = True


class EV1527:
    name = "EV1527"

    def __init__(self, sequence):
        self.sequence = sequence[:]
        self._ok = False
        self.code = "-"

    def ok(self):
        return self._ok

    def res(self):
        return "%s %s" % (self.name, self.code)

    # Transitions that are not 0-1 or 1-0, possibly due to some delay in
    # interrupt handling
    def false_transition(self):
        for i in range(0, len(self.sequence) - 1):
            if self.sequence[i][0] == self.sequence[i+1][0]:
                return (i, i+1)
        return None

    # Calculate average timing of each bit
    def bit_timing(self):
        tot = totsq = 0
        bitcount = len(self.sequence) // 2
        for i in range(0, bitcount):
            bittime = self.sequence[i*2][1] + self.sequence[i*2+1][1]
            tot += bittime
            totsq += bittime * bittime
        mean = tot / bitcount
        return mean, (totsq / bitcount - mean * mean) ** 0.5

    # Find if timing of a single bit is off
    def anomalous_bit_timing(self, std, dev):
        bitcount = len(self.sequence) // 2
        for i in range(0, bitcount):
            bit_time = self.sequence[i*2][1] + self.sequence[i*2+1][1]
            if bit_time < (std - dev) or bit_time > (std + dev):
                return (i, bit_time)
        return None

    # Find whether the length of a chirp is off
    def anomalous_chirp(self, short, shortdev, long, longdev):
        for i in range(0, len(self.sequence)):
            chirplen = self.sequence[i][1]
            if (chirplen >= (short - shortdev) and chirplen <= (short + shortdev)) or \
               (chirplen >= (long  - longdev)  and chirplen <= (long  + longdev)):
                pass
            else:
                return (i, chirplen)
        return None

    def do_parse(self):
        code = 0
        bitcount = len(self.sequence) // 2
        for i in range(0, bitcount):
            code <<= 1
            if self.sequence[i*2][1] > self.sequence[i*2+1][1]:
                # 1110 = bit 1
                code |= 1
        return code

    def run(self):
        false_trans = self.false_transition()
        if false_trans:
            print("> false trans %d-%d" % false_trans)
            return
        if len(self.sequence) != 49:
            print("> unexpected len")
            return
        self.sequence = self.sequence[:48]
        if self.sequence[0][0] != 1:
            print("> unexpected first chirp")
            return
        bit_time, bit_time_dev = self.bit_timing()
        print("> bit timing %dus stddev %dus" % (bit_time, bit_time_dev))
        anom = self.anomalous_bit_timing(bit_time, bit_time * 0.25)
        if anom:
            print("> bit timing anomaly %d timing %d" % anom)
            return
        anom = self.anomalous_chirp(bit_time * 0.25, bit_time * 0.25 * 0.25,
                                    bit_time * 0.75, bit_time * 0.25 * 0.25)
        if anom:
            print("> chirp timing anomaly %d timing %d" % anom)
            return
        code = self.do_parse()
        self.code = "%d" % code
        self._ok = True

parsers = [EV1527, HT6P20]

def parse(sequence):
    for parser_class in parsers:
        parser = parser_class(sequence)
        parser.run()
        if parser.ok():
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
