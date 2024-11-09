from machine import Pin
from time import ticks_us, ticks_add, ticks_diff
from micropython import schedule

last_timestamp = 0
irq_count = 0

TRANS_MAX = 200
trans_sequence = [ [0, 0] for _ in range(0, TRANS_MAX) ]
trans_length = 0
closed_sequence = [ [0, 0] for _ in range(0, TRANS_MAX) ]
closed_length = 0
closed_sequence_free = True

def parse_sequence(_):
    global closed_sequence_free
    print(closed_sequence[0:closed_length])
    closed_sequence_free = True

def irq(p):
    global last_timestamp, irq_count
    global trans_sequence, trans_length
    global closed_sequence, closed_length, closed_sequence_free

    # if value is 1, it means it has been 0
    v = not not p.value()

    t = ticks_us()
    dt = ticks_diff(t, last_timestamp)
    last_timestamp = t

    irq_count += 1

    if dt < 150 or dt > 50000 or trans_length >= (TRANS_MAX - 1):
        # bad transition
        if trans_length == 0:
            return

        # TODO handle long transitions as sequence terminators

        if trans_length > 10 and closed_sequence_free:
            # swap buffers
            closed_sequence, trans_sequence = trans_sequence, closed_sequence
            closed_length = trans_length
            closed_sequence_free = False
            schedule(parse_sequence, None)

        trans_length = 0
        return

    # good transition; annotate
    trans_sequence[trans_length][0] = v
    trans_sequence[trans_length][1] = dt
    trans_length += 1

pin = Pin(14, Pin.IN)
pin.irq(trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=irq)
