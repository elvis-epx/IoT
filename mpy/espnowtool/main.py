import sys, time
from espnowtool.proto import *
from espnowtool.utils import group_hash, prepare_key

def usage():
    print("Usage: entool <psk> <group> <channel> tx <packet type>")
    print("              <psk> <group> <channel> rx <timeout> <packet type>")
    sys.exit(1)

def rx():
    psk = prepare_key(sys.argv[1].encode())
    group = group_hash(sys.argv[2].encode())
    channel = int(sys.argv[3])
    timeout = int(sys.argv[5]) + time.time()
    pkttype = sys.argv[6]

    pkt = rx_packet(psk, group, channel, timeout, pkttype)
    if pkt:
        print("entool: received expected packet")
        sys.exit(0)
    print("entool: failed to receive expected packet")
    sys.exit(1)

def run():
    if len(sys.argv) < 7:
        usage()
    elif sys.argv[4] == "rx":
        rx()
    elif sys.argv[4] == "tx":
        tx()
    else:
        usage()
