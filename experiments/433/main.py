from machine import Pin
from time import ticks_us, ticks_add, ticks_diff
from micropython import schedule

last_timestamp = 0
last_value = 0
in_seq = False

sequence = []

def data_transition(pair):
    sequence.append(pair)

def close_sequence(_):
    global sequence
    seq = sequence
    sequence = []
    print(seq)

def irq(p):
    global last_timestamp, last_value, in_seq

    # if value is 1, it means it has been 0
    v = p.value()
    if v == last_value:
        return
    last_value = v

    t = ticks_us()
    dt = ticks_diff(t, last_timestamp)
    last_timestamp = t

    if dt < 150 or dt > 50000:
        # bad transition
        if in_seq:
            schedule(close_sequence, None)
            in_seq = False
        return

    # good transition
    # send !v instead of v since e.g. if it is 1, it has been 0 for time dt
    in_seq = True
    schedule(data_transition, (not not v, dt))

pin = Pin(14, Pin.IN)
pin.irq(trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=irq)
