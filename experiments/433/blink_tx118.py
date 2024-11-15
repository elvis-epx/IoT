from machine import Pin
import time
p = Pin(2, Pin.OUT)
p.value(1)

while True:
    p.value(0)
    time.sleep_ms(100)
    p.value(1)
    time.sleep(10)
