from machine import Pin
from time import ticks_us, ticks_add, ticks_diff
from micropython import schedule

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

def parse_sequence(_):
    global trans_sequence, trans_length, i, to_parse
    while to_parse > 0:
        j = (i - to_parse) % RING_BUF
        print(trans_sequence[j][0:trans_length[j]])
        to_parse -= 1

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

    if state == DATA:
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
            if to_parse == 1:
                schedule(parse_sequence, None)

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
