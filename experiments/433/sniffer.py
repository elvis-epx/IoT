from machine import Pin
from time import ticks_us, ticks_add, ticks_diff
from micropython import schedule

### Upper half

class OOKParser:
    # Generic ASK/OOK parser for 433MHz keyfobs
    # Assumptions:
    # - every bit is composed of two level transitions
    # - every bit has around the same total time length (i.e. the sum of the two transitions)

    name = ""
    bit_tolerance = 0.15
    group_tolerance = 0.25

    def __init__(self, sequence):
        self.sequence = sequence[:]
        self._ok = False
        self.code = "-"

    def ok(self):
        return self._ok

    def res(self):
        return "%s:%s" % (self.name, self.code)

    # Transitions that are not 0-1 or 1-0
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

    # Find whether the length of a chirp group is off
    def anomalous_group(self, short, shortdev, long, longdev):
        for i in range(0, len(self.sequence)):
            glen = self.sequence[i][1]
            if (glen >= (short - shortdev) and glen <= (short + shortdev)) or \
               (glen >= (long  - longdev)  and glen <= (long  + longdev)):
                pass
            else:
                return (i, glen)
        return None

    # Do the final conversion from transitions to bits
    # Assumes the transition list is sane
    def do_parse(self):
        code = 0
        bitcount = len(self.sequence) // 2
        for i in range(0, bitcount):
            code <<= 1
            if self.sequence[i*2][1] > self.sequence[i*2+1][1]:
                if self.bit1 == "LS":
                    code |= 1
            else:
                if self.bit1 == "SL":
                    code |= 1
        return code

    # Parsing routine
    def run(self):
        false_trans = self.false_transition()
        if false_trans:
            print(self.name, "> false trans %d-%d" % false_trans)
            return False

        if len(self.sequence) > self.exp_sequence_len:
            print(self.name, "> len too long")
            return False

        if len(self.sequence) < self.exp_sequence_len:
            print(self.name, "> len too short")
            return False

        if self.sequence[0][0] != 1:
            print(self.name, "> unexpected first chirp")
            return False

        if self.bitseq == "LH":
            # the first H transition is a delimiter
            self.sequence = self.sequence[1:self.exp_sequence_len + 1]
        else:
            # bits are HL; the last H transition is a delimiter
            self.sequence = self.sequence[0:self.exp_sequence_len - 1]

        bit_time, bit_time_dev = self.bit_timing()
        print(self.name, "> bit timing %dus stddev %dus" % (bit_time, bit_time_dev))

        anom = self.anomalous_bit_timing(bit_time, bit_time * self.bit_tolerance)
        if anom:
            print(self.name, "> bit timing anomaly %d timing %d" % anom)
            return False

        chirp_length = bit_time / self.chirp_length
        short_group = chirp_length * self.short_group
        long_group = chirp_length * self.long_group
        print(self.name, "> chirp timing %dus short %dus long %dus" % \
                (chirp_length, short_group, long_group))

        anom = self.anomalous_group(short_group, short_group * self.group_tolerance,
                                    long_group, long_group * self.group_tolerance)
        if anom:
            print(self.name, "> chirp timing anomaly %d timing %d" % anom)
            return False

        code = self.do_parse()
        self.code = "%d" % code
        self._ok = True
        

class HT6P20(OOKParser):
    name = "HT6P20"
    exp_sequence_len = 57
    bitseq = "LH" # low then high (011, 001)
    bit1 = "LS" # long then short (001)
    chirp_length = 3 # 1/x of a bit
    short_group = 1
    long_group = 2


class EV1527(OOKParser):
    name = "EV1527"
    exp_sequence_len = 49
    bitseq = "HL" # high then low (1000 and 1110)
    bit1 = "LS" # long then short (1110)
    chirp_length = 4 # 1/x of a bit
    short_group = 1
    long_group = 3


parsers = [EV1527, HT6P20]

def parse(sequence):
    print("----------------")
    print(sequence)
    for parser_class in parsers:
        parser = parser_class(sequence)
        parser.run()
        if parser.ok():
            print(parser.res())
            break
    else:
        print("Failed to parse")


#### Bottom half

IDLE = const(0)
DATA = const(1)
FULL = const(2)

last_timestamp = 0
irq_count = 0
state = IDLE

TRANS_MAX = const(100)
RING_BUF = const(10)
trans_sequence = [ [ [0, 0] for _ in range(0, TRANS_MAX) ] for _ in range(0, RING_BUF) ]
trans_length = [ 0 for _ in range(0, RING_BUF) ]
i = 0
to_parse = 0

# Typical preamble length is 10k-12kµs
PREAMBLE_MIN = const(6000)
PREAMBLE_MAX = const(20000)
# EV1527 = 230µs, HT6P20 = 500µs
DATA_MIN = const(120)
# EV1527 = 3x min, HT6P20 = 2x min
DATA_MAX = const(1800)
# 24 bits = 48 transitions for EV1527, 28 bits for HT6P20
TRANS_COUNT_MIN = const(30)

def irq(p):
    global last_timestamp, irq_count, state
    global trans_sequence, trans_length
    global i, to_parse

    # if value is 1, it means it has been 0
    v = (p.value() + 1) % 2

    # Calculate pulse length
    t = ticks_us()
    dt = ticks_diff(t, last_timestamp)
    last_timestamp = t

    irq_count += 1

    if state == FULL:
        if to_parse >= RING_BUF:
            return
        state = IDLE

    if state == IDLE:
        if dt > PREAMBLE_MIN and dt < PREAMBLE_MAX and v == 0:
            # detected preamble
            state = DATA
            trans_length[i] = 0
        return

    # state == DATA

    if dt > DATA_MIN and dt < DATA_MAX:
        # chirps of data
        trans_sequence[i][trans_length[i]][0] = v
        trans_sequence[i][trans_length[i]][1] = dt
        trans_length[i] += 1
        if trans_length[i] >= TRANS_MAX:
            # overflow, discard
            state = IDLE
        return

    # Sequence terminated by silence or bad transition
    state = IDLE

    if trans_length[i] > TRANS_COUNT_MIN:
        # Export ongoing sequence
        to_parse += 1
        i = (i + 1) % RING_BUF

        if to_parse >= RING_BUF:
            # Must not overwrite the buffer pointed by "i" for now
            state = FULL
            return

    if dt > PREAMBLE_MIN and dt < PREAMBLE_MAX and v == 0:
        # new preamble (back-to-back packet)
        # short-circuit state machine to DATA
        trans_length[i] = 0
        state = DATA

pin = Pin(14, Pin.IN)
pin.irq(trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=irq)


### Main routine

while True:
    if to_parse == 0:
        continue

    j = (i - to_parse) % RING_BUF
    parse(trans_sequence[j][0:trans_length[j]])
    to_parse -= 1
