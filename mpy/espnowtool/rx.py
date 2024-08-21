from espnowtool.utils import *
import time
import os

pkttypes = {"pairreq": type_pairreq, "data": type_data, "ts": type_timestamp}

def rx_packet(psk, group, channel, timeout, pkttypename, args):
    folder = os.environ["TEST_FOLDER"] + "/espnow_packets/"
    while time.time() < timeout:
        if pkt := rx_packet_in(folder, psk, group, channel, pkttypes[pkttypename], args):
            return pkt
        time.sleep(0.1)
    return None

def rx_packet_in(folder, psk, group, channel, exptype, args):
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

        if channel != 0 and pkt_channel != channel:
            print("entool: recv for channel %d expected %d" % (pkt_channel, channel))
        elif pkt_dmac != my_mac and pkt_dmac != broadcast_mac:
            print("entool: recv for mac that is not me", pkt_dmac)
        else:
            return rx_packet_in2(psk, group, exptype, pkt_smac, pkt_data, args)

def rx_packet_in2(psk, group, exptype, smac, msg, args):
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
    res = {"raw": msg}
    res = handlers[pkttype](msg, args, res)
    return res

# as central (for now)
def rx_data(msg, args, res):
    timestamp, msg = decode_timestamp(msg[0:timestamp_size]), msg[timestamp_size:]
    tid, msg = b2s(msg[0:tid_size]), msg[tid_size:]
    data = msg
    diff = int(time.time() * 1000) - timestamp
    res["data"] = data
    print("entool: Data received", data, "timestamp", timestamp, diff, "tid", tid)
    return res

# as peripheral
def rx_timestamp(msg, args, res):
    subtype, msg = msg[0], msg[1:]
    ts_tid, msg = b2s(msg[0:tid_size]), msg[tid_size:]
    timestamp, msg = decode_timestamp(msg[0:timestamp_size]), msg[timestamp_size:]
    confirm_tid = None
    if subtype == timestamp_subtype_confirm:
        confirm_tid = b2s(msg[0:tid_size])

    folder = os.environ["TEST_FOLDER"] + "/espnow_packets/"

    good = False
    if 'confirm' in args:
        if subtype != timestamp_subtype_confirm:
            print("entool: ts not confirm type")
        elif 'tid' in args:
            if args['tid'] == 'lasttx':
                expected_tid = open(folder + 'tx_tid').read()
            else:
                expected_tid = args['tid']
            if confirm_tid != expected_tid:
                print("entool: ts confirm wrong sid recv", confirm_tid, "expected", expected_tid)
            else:
                print("entool: ts confirm tid", confirm_tid)
                good = True
        else:
            good = True
    else:
        if subtype != timestamp_subtype_default:
            print("entool: ts not default type")
        else:
            good = True
        
    if good:
        print("entool: ts received")
        open(folder + "ts_tid", "w").write(ts_tid)
        open(folder + "ts", "w").write("%d %d" % (timestamp, time.time() * 1000))
        if confirm_tid:
            open(folder + "confirm_tid", "w").write(confirm_tid)

    return good and res or None

# as central
def rx_pairreq(msg, args, res):
    print("entool: pairreq received")
    return res

handlers = {type_pairreq: rx_pairreq, type_data: rx_data, type_timestamp: rx_timestamp}
