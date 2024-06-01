import network, espnow, time

sta = network.WLAN(network.STA_IF); sta.active(False)
sta.active(True)
sta.config(channel=1)

e = espnow.ESPNow()
e.active(True)
e.set_pmk("foobar7890123456") # must be after active(True)

peer = bytes(int(x, 16) for x in "c4:dd:57:ea:90:e0".split(":"))
e.add_peer(peer, "barfoo7890123456")
counter = 0

while True:
    counter += 1
    counter %= 100
    if e.send(peer, b'ping %d' % counter):
        print("Sent")
    else:
        print("Not sent")
    time.sleep(3)
