from hx711 import HX711
import time

b = HX711(d_out=5, pd_sck=4)
while True:
    samples = []
    for i in range(0, 100):
        v = b.read()
        print(v)
        samples.append(v)
    mean = sum(samples) / len(samples)
    print("Mean: ", mean)
    var = sum([((x - mean) ** 2) for x in samples]) / len(samples)
    print("Stddev: ", var ** 0.5)
    time.sleep(10)
