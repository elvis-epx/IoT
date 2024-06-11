import network, espnow, time

# May be created before wlan
e = espnow.ESPNow()

sta = network.WLAN(network.STA_IF); sta.active(False)
sta.active(True)
sta.config(channel=1) # after active(True)

e.active(True)
e.set_pmk("foobarfoobarfoobar"[0:16]) # must be after active(True) and must have 16 chars

peer = bytes(int(x, 16) for x in "c4:dd:57:ea:90:e0".split(":"))
e.add_peer(peer, "barfoobarfoobarfoo"[0:16]) # must have 16 chars
counter = 0

while True:
    counter += 1
    
    if counter == 5:
        print("Restarting wifi")
        sta.active(False)
        time.sleep(1)
        sta.active(True)
        time.sleep(1)
        # silent fails after here
        print("Restarting espnow")
        e.active(True)
        # still fails after here
        e.set_pmk("foobarfoobarfoobar"[0:16]) # must be after active(True) and must have 16 chars
        # needs del and add to properly restart (though add will fail saying it already exists)
        e.del_peer(peer)
        e.add_peer(peer, "barfoobarfoobarfoo"[0:16]) # must have 16 chars

    # possible ETIMEOUT if sync = True
    if e.send(peer, b'ping %d' % counter, False):
        print("Sent", counter)
    else:
        print("Not sent", counter)
    time.sleep(2)
