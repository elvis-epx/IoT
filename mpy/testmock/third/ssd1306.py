import machine
import os
import os.path

ok = True

def test_mock():
    global ok
    f = "ssd1306f.sim"
    if os.path.exists(f):
        print("Got ssd1306f.sim")
        os.remove(f)
        ok = False
    
class SSD1306_I2C:
    def __init__(self, x, y, i2c):
        if not ok:
            raise OSError()
        pass

    def fill(self, color):
        pass

    def fill_rect(self, x, y, w, h, c):
        pass

    def rect(self, x, y, w, h, c):
        pass

    def text(self, s, x, y):
        pass

    def show(self):
        if not ok:
            raise OSError()
        pass
