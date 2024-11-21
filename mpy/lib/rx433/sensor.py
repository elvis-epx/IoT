from epx.loop import Task, MILISSECONDS, SECONDS, MINUTES
from epx import loop
import machine, esp32
# Uses custom MP https://github.com/elvis-epx/micropython/blob/rmt_rx/ports/esp32/esp32_rmt2.c

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
            bittime = abs(self.sequence[i*2+lh]) + abs(self.sequence[i*2+1+lh])
            tot += bittime
            totsq += bittime * bittime
        mean = tot / bitcount
        return mean, (totsq / bitcount - mean * mean) ** 0.5

    # Find if timing of a single bit is off
    def anomalous_bit_timing(self, bitcount, lh, std, dev):
        for i in range(0, bitcount):
            bit_time = abs(self.sequence[i*2+lh]) + abs(self.sequence[i*2+1+lh])
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
            lsbit = (abs(self.sequence[i*2+lh]) > abs(self.sequence[i*2+1+lh])) and 1 or 0
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

parsers = [EV1527, HT6P20]

### OOK decoding - bottom half

class OOKReceiver:
    # Typical preamble length is 10k-12kµs
    PREAMBLE_MIN_NS = const(5000 * 1000)
    # EV1527 = 230µs, HT6P20 = 500µs
    DATA_MIN_US = const(150)
    # EV1527 = 3x min, HT6P20 = 2x min
    DATA_MAX_US = const(1500)
    # 24 bits = 48 transitions for EV1527, 28 bits for HT6P20

    def __init__(self, observer):
        self.stats_ok = 0
        self.stats_nok1 = 0
        self.stats_nok2 = 0
        self.expected_lengths = [ c.exp_sequence_len for c in parsers ]
        self.observer = observer
        self.rmt = None

        # Delay startup to after the watchdog is active (10s)
        startup_time = hasattr(machine, 'TEST_ENV') and 1 or 12
        Task(False, "start", self.start, startup_time * SECONDS)

    def start(self, _):
        pin = machine.Pin(14, machine.Pin.IN)
        # ideally min_ns would be DATA_MIN_US * 1000 / 4 or so for better filtering,
        # but current RMT API does not support bigger values
        self.rmt = esp32.RMT2(pin=pin, buf=64, \
                              min_ns=3100, max_ns=self.PREAMBLE_MIN_NS, \
                              resolution_hz=1000000)
        loop.poll_object("RMT", self.rmt, loop.POLLIN, self.recv)
        self.rmt.read_pulses()

    def recv(self, _):
        data = self.rmt.get_data()
        if not data:
            return

        if len(data) not in self.expected_lengths:
            self.stats_nok2 += 1
            return
    
        for sample in data:
            abs_sample = abs(sample)
            if abs_sample < self.DATA_MIN_US or abs_sample > self.DATA_MAX_US:
                self.stats_nok1 += 1
                return

        self.stats_ok += 1
        self.observer.recv(data)

    def stop(self):
        if not self.rmt:
            return
        self.rmt.stop_read_pulses()
        self.rmt = None
    
    def stats(self):
        return "ook_ok=%d ook_nok1=%d ook_nok2=%d" % \
                (self.receiver.stats_ok, self.receiver.stats_nok1, self.receiver.stats_nok2)

### OOK decoding - glue and front-end class

class KeyfobRX:
    def __init__(self, mqttpub):
        self.mqttpub = mqttpub
        self.receiver = OOKReceiver(self)
        self.received = 0
        self.good = 0
        self.bad = 0

    def recv(self, data):
        self.received += 1
        print("--- received data, length %d" % len(data))
        for parser_class in parsers:
            parser = parser_class(data)
            if parser.parse():
                self.good += 1
                res = parser.res()
                print(res)
                self.mqttpub.new_value(res)
                break
        else:
            print("... failed to parse")
            self.bad += 1

    def stop(self):
        self.receiver.stop()

    def stats(self):
        return ("recv=%d good=%d bad=%d " % (self.received, self.good, self.bad)) + \
               self.receiver.stats()
