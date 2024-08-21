from espnowtool.utils import *
import time
import os

pkttypes = {"pairreq": type_pairreq}

def rx_packet(psk, group, channel, timeout, pkttypename):
    folder = os.environ["TEST_FOLDER"] + "/espnow_packets/"
    while time.time() < timeout:
        if pkt := rx_packet_in(folder, psk, group, channel, pkttypes[pkttypename]):
            return pkt
        time.sleep(0.1)
    return None

def rx_packet_in(folder, psk, group, channel, exptype):
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".tx"):
            continue
        rawdata = open(folder + f, "rb").read()
        os.unlink(folder + f)

        if len(rawdata) < 13:
            print("espnow mock: invalid packet")
            continue

        pkt_channel = int(rawdata[0])
        pkt_dmac = rawdata[1:7]
        pkt_smac = rawdata[7:13]
        pkt_data = rawdata[13:]

        if pkt_channel != channel:
            print("entool: recv for channel I am not listening")
        elif pkt_dmac != b"\x00\x01\x02\x03\x04\x05" and pkt_dmac != broadcast_mac:
            print("entool: recv for mac that is not me")
        else:
            return rx_packet_in2(psk, group, exptype, pkt_smac, pkt_data)

def rx_packet_in2(psk, group, exptype, smac, msg):
    if not check_hmac(psk, msg): 
        print("entool: bad hmac") 
        return 

    msg = msg[:-hmac_size] 
    msg = decrypt(psk, msg) 
    if msg is None:
        print("entool: cannot decrypt")
        return None

    if len(msg) < 2 + group_size:
        print("entool: invalid len")
        return None

    if msg[0] != version:
        print("entool: unknown version", version)
        return None

    pkttype = msg[1]
    pktgroup = msg[2:2+group_size]
    if pktgroup != group:
        print("entool: pkt group", pktgroup, "expected", group)
        return None
    if exptype != pkttype:
        print("entool: type expected", exptype, "received", pkttype)
        return None

    msg = msg[2+group_size:]
    return {"raw": msg}
