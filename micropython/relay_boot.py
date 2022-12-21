import machine

# Shortcut because of complementary-logic relay
machine.Pin(25, machine.Pin.OUT).value(1)
machine.Pin(26, machine.Pin.OUT).value(1)
machine.Pin(27, machine.Pin.OUT).value(1)
machine.Pin(33, machine.Pin.OUT).value(1)
machine.freq(80000000)
