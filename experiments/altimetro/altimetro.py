from lib.third import bme280
from machine import I2C, Pin
import time
i2c = I2C(0, sda=Pin(21), scl=Pin(22))
from third.bme280 import BME280, BME280_OSAMPLE_8
bme280 = BME280(i2c=i2c, mode=BME280_OSAMPLE_8)
while True:
    x = bme280.read_pressure() / 25600.0
    (((1013.0 / x) ** (1 / 5.257) - 1) * (20 + 273.15)) / 0.0065
    time.sleep(1)
