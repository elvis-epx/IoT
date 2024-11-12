from machine import Pin
from time import ticks_us, ticks_add, ticks_diff, time
from micropython import schedule

### Upper half

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

    # Calculate average timing of each bit
    def bit_timing(self):
        tot = totsq = 0
        bitcount = len(self.sequence) // 2
        lh = (self.bitseq == "LH") and 1 or 0
        for i in range(0, bitcount):
            bittime = self.sequence[i*2+lh][1] + self.sequence[i*2+1+lh][1]
            tot += bittime
            totsq += bittime * bittime
        mean = tot / bitcount
        return mean, (totsq / bitcount - mean * mean) ** 0.5

    # Find if timing of a single bit is off
    def anomalous_bit_timing(self, std, dev):
        bitcount = len(self.sequence) // 2
        lh = (self.bitseq == "LH") and 1 or 0
        for i in range(0, bitcount):
            bit_time = self.sequence[i*2+lh][1] + self.sequence[i*2+1+lh][1]
            if bit_time < (std - dev) or bit_time > (std + dev):
                return (i, bit_time)
        return None

    # Parsing routine
    def parse(self):
        if len(self.sequence) != self.exp_sequence_len:
            return False

        bit_time, bit_time_dev = self.bit_timing()
        print(self.name, "> bit timing %dus stddev %dus" % (bit_time, bit_time_dev))

        anom = self.anomalous_bit_timing(bit_time, bit_time * 0.15)
        if anom:
            print(self.name, "> bit timing anomaly %d timing %d" % anom)
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

epoch = time()

def parse(sequence):
    print("----------------")
    print("time %d" % (time() - epoch))
    print(sequence)
    print("length %d" % len(sequence))
    for parser_class in parsers:
        parser = parser_class(sequence)
        if parser.parse():
            print(parser.res())
            break
    else:
        print("Failed to parse")


#### Bottom half

IDLE = const(0)
DATA = const(1)
FULL = const(2)

last_timestamp = 0
last_v = -1
state = IDLE

TRANS_MAX = const(100)
RING_BUF = const(10)
trans_sequence = [ [ [0, 0] for _ in range(0, TRANS_MAX) ] for _ in range(0, RING_BUF) ]
trans_length = [ 0 for _ in range(0, RING_BUF) ]
i = 0
to_parse = 0

# Typical preamble length is 10k-12kµs
PREAMBLE_MIN = const(5000)
PREAMBLE_MAX = const(20000)
# EV1527 = 230µs, HT6P20 = 500µs
DATA_MIN = const(150)
# EV1527 = 3x min, HT6P20 = 2x min
DATA_MAX = const(1500)
# 24 bits = 48 transitions for EV1527, 28 bits for HT6P20
TRANS_COUNT_MIN = const(40)

def irq(p):
    global last_timestamp, last_v, state
    global trans_sequence, trans_length
    global i, to_parse

    # if value is 1, it means it has been 0
    v = (p.value() + 1) % 2
    if v == last_v:
        # false transition, ignore
        return
    last_v = v

    # Calculate pulse length
    t = ticks_us()
    dt = ticks_diff(t, last_timestamp)
    last_timestamp = t

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
