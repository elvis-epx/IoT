from epx.loop import Task, MILISSECONDS, SECONDS, MINUTES
from epx import loop
from machine import Pin
from time import ticks_us, ticks_add, ticks_diff

### OOK decoder - Upper half

class OOKParser:
    # Generic ASK/OOK parser for 433MHz keyfobs
    # Assumption: every bit is composed of two level transitions

    name = ""
    bit_len_tolerance = 0.15

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
        self.sequence = sequence
        self.code = 0

    def res(self):
        return "%s:%d" % (self.name, self.code)

    # Calculate average timing of each bit
    def bit_timing(self, bitcount, lh):
        tot = totsq = 0
        for i in range(0, bitcount):
            bittime = self.sequence[i*2+lh][1] + self.sequence[i*2+1+lh][1]
            tot += bittime
            totsq += bittime * bittime
        mean = tot / bitcount
        return mean, (totsq / bitcount - mean * mean) ** 0.5

    # Find if timing of a single bit is off
    def anomalous_bit_timing(self, bitcount, lh, std, dev):
        for i in range(0, bitcount):
            bit_time = self.sequence[i*2+lh][1] + self.sequence[i*2+1+lh][1]
            if bit_time < (std - dev) or bit_time > (std + dev):
                return (i, bit_time)
        return None

    # Parsing routine
    def parse(self):
        if len(self.sequence) != self.exp_sequence_len:
            return False

        bitcount = len(self.sequence) // 2
        lh = (self.bitseq == "LH") and 1 or 0
        ls = (self.bitseq == "LS") and 1 or 0

        bit_time, bit_time_dev = self.bit_timing(bitcount, lh)
        print(self.name, "> bit timing %dus stddev %dus" % (bit_time, bit_time_dev))

        anom = self.anomalous_bit_timing(bitcount, lh, bit_time, bit_time * self.bit_len_tolerance)
        if anom:
            print(self.name, "> bit timing anomaly %d timing %d" % anom)
            return False

        # Parse sane sequence
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

    def parse(self):
        if not super().parse():
            return False
        if (self.code & 0xf) != 0b0101:
            print(self.name, "> suffix 0101 not found")
            return False
        return True

class EV1527(OOKParser):
    name = "EV1527"
    exp_sequence_len = 49
    bitseq = "HL" # high then low (1000 and 1110)
    bit1 = "LS" # long then short (1110)

### OOK decoding - bottom half

class OOKReceiver:
    IDLE = const(0)
    DATA = const(1)
    FULL = const(2)
    TRANS_MAX = const(100)
    RING_BUF = const(10)
    # Typical preamble length is 10k-12kµs
    PREAMBLE_MIN = const(5000)
    PREAMBLE_MAX = const(20000)
    # EV1527 = 230µs, HT6P20 = 500µs
    DATA_MIN = const(150)
    # EV1527 = 3x min, HT6P20 = 2x min
    DATA_MAX = const(1500)
    # 24 bits = 48 transitions for EV1527, 28 bits for HT6P20
    TRANS_COUNT_MIN = const(40)

    def __init__(self):
        self.trans_sequence = [ [ [0, 0] for _ in range(0, self.TRANS_MAX) ] for _ in range(0, self.RING_BUF) ]
        self.trans_length = [ 0 for _ in range(0, self.RING_BUF) ]

        self.last_timestamp = 0
        self.last_v = -1
        self.i = 0
        self.to_parse = 0
        self.state = self.IDLE

        self.pin = Pin(14, Pin.IN)
        self.pin.irq(trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.irq)

    def irq(self, p):
        # if value is 1, it means it has been 0
        v = (p.value() + 1) % 2
        if v == self.last_v:
            # false transition, ignore
            return
        self.last_v = v
    
        # Calculate pulse length
        t = ticks_us()
        dt = ticks_diff(t, self.last_timestamp)
        self.last_timestamp = t
    
        if self.state == self.FULL:
            if self.to_parse >= self.RING_BUF:
                return
            self.state = self.IDLE
    
        if self.state == self.IDLE:
            if dt > self.PREAMBLE_MIN and dt < self.PREAMBLE_MAX and v == 0:
                # detected preamble
                self.state = self.DATA
                self.trans_length[self.i] = 0
            return
    
        # state == DATA
    
        if dt > self.DATA_MIN and dt < self.DATA_MAX:
            # chirps of data
            self.trans_sequence[self.i][self.trans_length[self.i]][0] = v
            self.trans_sequence[self.i][self.trans_length[self.i]][1] = dt
            self.trans_length[self.i] += 1
            if self.trans_length[self.i] >= self.TRANS_MAX:
                # overflow, discard
                self.state = self.IDLE
            return
    
        # Sequence terminated by silence or bad transition
        self.state = self.IDLE
    
        if self.trans_length[self.i] > self.TRANS_COUNT_MIN:
            # Export ongoing sequence
            self.to_parse += 1
            self.i = (self.i + 1) % self.RING_BUF
    
            if self.to_parse >= self.RING_BUF:
                # Must not overwrite the buffer pointed by "i" for now
                self.state = self.FULL
                return
    
        if dt > self.PREAMBLE_MIN and dt < self.PREAMBLE_MAX and v == 0:
                # new preamble (back-to-back packet)
            # short-circuit state machine to DATA
            self.trans_length[self.i] = 0
            self.state = self.DATA
    
    def get_data(self):
        if self.to_parse == 0:
            return None

        j = (self.i - self.to_parse) % self.RING_BUF
        data = self.trans_sequence[j][0:self.trans_length[j]]
        data = [ a[:] for a in data ]
        self.to_parse -= 1

        return data

### OOK decoding - glue and front-end class

class KeyfobRX:
    def __init__(self, mqttpub):
        self.mqttpub = mqttpub
        self.eval_task = Task(True, "eval", self.eval, 500 * MILISSECONDS)
        self.parsers = [EV1527, HT6P20]
        self.receiver = OOKReceiver()

    def eval(self, _):
        data = self.receiver.get_data()
        if not data:
            return
        print("----------------")
        print(data)
        print("length %d" % len(data))
        for parser_class in self.parsers:
            parser = parser_class(data)
            if parser.parse():
                res = parser.res()
                print(res)
                self.mqttpub.new_value(res)
                break
        else:
            print("Failed to parse")
