import LoRaDuplexCallback
from ttgolora import TTGOLoRa
import ssd1306
from ssd1306 import SSD1306_I2C
from time import sleep_ms
from machine import Pin, SoftI2C, Signal
from micropython import const

lora = TTGOLoRa().lora

OLED_RST = const(16)  # FIXME get from Lora32v1_0 in Micropython 1.20
OLED_SDA = const(4)
OLED_SCL = const(15)
i2c = SoftI2C(scl=Pin(OLED_SCL), sda=Pin(OLED_SDA))
rstpin = Pin(OLED_RST, Pin.OUT)

rstpin.value(0)
sleep_ms(50)
rstpin.value(1)
display = SSD1306_I2C(128, 32, i2c) # FIXME use Micropython post 1.20 fixed version
display.fill(0)
display.text("hello", 0, 0, 1)
display.show()

LoRaDuplexCallback.duplexCallback(lora, display)
