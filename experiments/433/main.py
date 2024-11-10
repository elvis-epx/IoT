from machine import Pin
from time import ticks_us, ticks_add, ticks_diff
from micropython import schedule

IDLE = 0
DATA = 1
FULL = 2

last_timestamp = 0
irq_count = 0
state = IDLE

TRANS_MAX = 100
RING_BUF = 10
trans_sequence = [ [ [0, 0] for _ in range(0, TRANS_MAX) ] for _ in range(0, RING_BUF) ]
trans_length = [ 0 for _ in range(0, RING_BUF) ]
i = 0
ready = 0

def parse_sequence(_):
    global trans_sequence, trans_length, i, ready
    while ready > 0:
        j = (i - ready) % RING_BUF
        print(trans_sequence[j][0:trans_length[j]])
        ready -= 1

def irq(p):
    global last_timestamp, irq_count
    global trans_sequence, trans_length
    global i, ready, state

    # if value is 1, it means it has been 0
    v = not not p.value()

    t = ticks_us()
    dt = ticks_diff(t, last_timestamp)
    last_timestamp = t

    irq_count += 1

    if state == FULL:
        if ready >= RING_BUF:
            return
        state = IDLE

    if state == IDLE:
        if dt > 6000 and dt < 100000 and not v:
            # detected preamble
            state = DATA
            trans_length[i] = 0
        return

    if state == DATA:
        if dt > 150 and dt < 1500:
            # chirps of data
            trans_sequence[i][trans_length[i]][0] = v
            trans_sequence[i][trans_length[i]][1] = dt
            trans_length[i] += 1
            if trans_length[i] >= TRANS_MAX:
                # overflow, discard
                state = IDLE
            return

        # Sequence terminated by silence or bad transition
        if trans_length[i] > 20:
            # Export sequence
            ready += 1
            i = (i + 1) % RING_BUF
            schedule(parse_sequence, None)

            if ready >= RING_BUF:
                # Must not overwrite the buffer pointed by "i" for now
                state = FULL
                return

        state = IDLE

        if dt > 6000 and dt < 100000 and not v:
            # new preamble (back-to-back packet)
            # short-circuit state machine to DATA
            trans_length[i] = 0
            state = DATA

pin = Pin(14, Pin.IN)
pin.irq(trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=irq)
