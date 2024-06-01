import network, espnow, time

sta = network.WLAN(network.STA_IF); sta.active(False)
sta.config(channel=6)
sta.active(True)

e = espnow.ESPNow()
e.active(True)
e.set_pmk("foobar7890123456")
peer = bytes(int(x, 16) for x in "c8:f0:9e:4d:09:0c".split(":"))
e.add_peer(peer, "barfoo7890123456")

while True:
    if e.any():
        print(e.recv())
        print(e.peers_table)
    else:
        print("No data")
    time.sleep(2)
