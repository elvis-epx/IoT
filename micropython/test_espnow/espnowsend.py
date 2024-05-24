import network, espnow, time

sta = network.WLAN(network.STA_IF); sta.active(False)
sta.active(True)
sta.config(channel=6)

e = espnow.ESPNow()
e.active(True)

peer = b'\xff' * 6
e.add_peer(peer)
counter = 0

while True:
    counter += 1
    e.send(peer, b'ping %d' % counter)
    print("Sent")
    time.sleep(1)
