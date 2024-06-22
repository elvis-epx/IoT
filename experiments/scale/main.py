from hx711 import HX711, HX711Exception
import time

a = 28276.0
b = 36759.0

device = HX711(d_out=5, pd_sck=4)
while True:
    samples = []
    for i in range(0, 3):
        time.sleep(1)
        v = device.read()
        # print(v)
        samples.append(v)
    mean = sum(samples) / len(samples)
    var = sum([((x - mean) ** 2) for x in samples]) / len(samples)
    weight = (mean + b) / a
    print("Mean: ", mean, "Stddev: ", var ** 0.5, var * 0.5 / a, "Weight", weight)
