import network, espnow, time

sta = network.WLAN(network.STA_IF); sta.active(False)
sta.active(True)
sta.config(channel=1) # must be after active(true)

e = espnow.ESPNow()
e.active(True)
e.set_pmk("foobarfoobarfoobar"[0:16]) # must have 16 chars
peer = bytes(int(x, 16) for x in "c8:f0:9e:4d:09:0c".split(":"))
e.add_peer(peer, "barfoobarfoobarfoo"[0:16]) # must have 16 chars

while True:
    if e.any():
        print(e.recv())
        print(e.peers_table)
    else:
        print("No data")
    time.sleep(2)
