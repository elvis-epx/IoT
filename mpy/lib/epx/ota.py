import gc
from epx import loop
import machine
from epx.loop import StateMachine, Task, SECONDS, MILISSECONDS
import os
from hashlib import sha1
import binascii

if hasattr(machine, 'TEST_ENV'):
    import socket
    sockerror = (IOError,)
    def eagain(e):
        return isinstance(e, BlockingIOError)
    def setuplistener(s):
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    root = "."
else: # pragma: no cover
    import usocket as socket
    sockerror = (OSError,)
    def eagain(e):
        return e.value == 11
    def setuplistener(s):
        pass
    root = ""

class OTAHandler:
    def __init__(self):
        self.sock = socket.socket()
        self.sock.setblocking(False)
        setuplistener(self.sock)
        self.sock.bind(('0.0.0.0', 1337))
        self.sock.listen(1)

        sm = self.sm = StateMachine("ota")

        sm.add_state("listen", self.on_listen)
        sm.add_state("header", self.on_header)
        sm.add_state("payload", self.on_payload)
        sm.add_state("eof", self.on_eof)
        sm.add_state("done", self.on_done)
        sm.add_state("connlost", self.on_connlost)

        sm.add_transition("initial", "listen")
        sm.add_transition("listen", "header")
        sm.add_transition("header", "connlost")
        sm.add_transition("header", "done")
        sm.add_transition("header", "payload")
        sm.add_transition("payload", "connlost")
        sm.add_transition("payload", "eof")
        sm.add_transition("eof", "connlost")
        sm.add_transition("eof", "done")
        sm.add_transition("done", "listen")
        sm.add_transition("connlost", "listen")
        
        self.connection = None
        self.tmpfile = None

        upl = [ f for f in os.listdir(root) if f.endswith(".upl") ]
        for f in upl:
            try:
                print("Removing", f)
                os.unlink(f)
            except OSError as e:
                print("OTA rm %s fail" % f)

        self.sm.schedule_trans("listen", 1 * SECONDS)

    def on_listen(self):
        self.buf = None
        if self.connection:
            self.connection.close()
            self.connection = None
        if self.tmpfile:
            self.tmpfile.close()
            self.tmpfile = None
        self.uplfilename = ''
        self.filelen = 0
        gc.collect()
        self.sm.recurring_task("ota_listen", self.listen_poll, 500 * MILISSECONDS)

    def on_connlost(self):
        self.sm.schedule_trans_now("listen")

    def listen_poll(self, _):
        try:
            self.connection, _ = self.sock.accept()
        except sockerror as e:
            # could be EAGAIN or not, either case, can't do anything about
            return
        self.connection.setblocking(False)
        self.sm.schedule_trans_now("header")

    def on_header(self):
        self.buf = b''
        self.sm.recurring_task("ota_header", self.header_poll, 500 * MILISSECONDS)
        self.sm.schedule_trans("connlost", 10 * SECONDS)

    def read(self):
        try:
            data = self.connection.recv(1500)
        except sockerror as e:
            if eagain(e):
                return 0, None

            print("OTA: recv() fail")
            self.sm.schedule_trans_now("connlost")
            return -1, None

        if len(data) == 0:
            print("OTA: recv() EOF")
            self.sm.schedule_trans_now("connlost")
            return -2, None

        return 1, data
     
    def header_poll(self, _):
        res, data = self.read()
        if res <= 0:
            return

        self.buf += data
        res, ptype = self.parse_packet({1: 6, 5: 4, 7: 4})
        if res <= 0:
            return

        if ptype == 1:
            self.header_to_payload()
        elif ptype == 5:
            self.header_to_hash()
        elif ptype == 7:
            self.header_to_rm()
        else:
            self.sm.schedule_trans_now("connlost")

    def encodeuplfile(self, f):
        return f.replace("/", "$") + ".upl"

    def decodeuplfile(self, f):
        return f[:-4].replace("$", "/")

    def header_to_payload(self):
        self.filelen = self.buf[2] * 256 + self.buf[3]
        self.filetot = 0
        filename = self.buf[4:-1].decode('ascii')
        self.tmpfilename = 'tmppiggy'
        if hasattr(machine, 'TEST_ENV'):
            filename = machine.TEST_FOLDER + filename
            self.tmpfilename = machine.TEST_FOLDER + self.tmpfilename
        self.tmpfile = open(self.tmpfilename, 'wb')
        self.uplfilename = self.encodeuplfile(filename)
        print("OTA file %s len %d" % (self.uplfilename, self.filelen))
        self.buf = b''
        gc.collect()

        try:
            self.connection.send(b'1')
        except sockerror as e:
            print("Failure while acking header")
            self.sm.schedule_trans_now("connlost")
            return

        self.sm.schedule_trans_now("payload")

    def header_to_hash(self):
        filename = self.buf[2:-1].decode('ascii')
        self.buf = b''

        if hasattr(machine, 'TEST_ENV'):
            filename = machine.TEST_FOLDER + filename
        try:
            h = sha1()
            f = open(filename, 'rb')
            while True:
                data = f.read(64)
                if not data:
                    break
                h.update(data)
                gc.collect()
            h = binascii.hexlify(h.digest())
        except OSError as e:
            h = b'0' * 40

        print("OTA file %s hash %s" % (filename, h))

        try:
            self.connection.send(b'6' + h)
        except sockerror as e:
            print("Failure while answering hash")
            self.sm.schedule_trans_now("connlost")
            return

        self.sm.schedule_trans_now("done")

    def header_to_rm(self):
        filename = self.buf[2:-1].decode('ascii')
        self.buf = b''

        if hasattr(machine, 'TEST_ENV'):
            filename = machine.TEST_FOLDER + filename
        try:
            os.unlink(filename)
            print("OTA file rm %s" % filename)
        except OSError as e:
            print("OTA file rm %s fail" % filename)

        try:
            self.connection.send(b'8')
        except sockerror as e:
            print("Failure while answering rm")
            self.sm.schedule_trans_now("connlost")
            return

        self.sm.schedule_trans_now("done")

    def parse_packet(self, exp_types):
        if len(self.buf) < 3:
            return 0, 0

        length, ptype = self.buf[0], self.buf[1]

        if ptype not in exp_types:
            print("Unexpected pkt type")
            self.sm.schedule_trans_now("connlost")
            return -1, 0

        min_len = exp_types[ptype]

        if length < min_len:
            print("Unexpectedly short pkt len")
            self.sm.schedule_trans_now("connlost")
            return -1, 0

        if len(self.buf) < length:
            return 0, 0

        if len(self.buf) > length:
            print("Pkt too long")
            self.sm.schedule_trans_now("connlost")
            return -1, 0

        checksum = 0
        for b in self.buf:
            checksum ^= b
        if checksum != 0:
            print("Invalid checksum")
            self.sm.schedule_trans_now("connlost")
            return -1, 0

        return 1, ptype

    def on_payload(self):
        self.sm.recurring_task("ota_payload", self.payload_poll, 50 * MILISSECONDS)
        self.sm.schedule_trans("connlost", 30 * SECONDS)

    def payload_poll(self, _):
        res, data = self.read()
        if res <= 0:
            return

        self.buf += data
        res, _ = self.parse_packet({2: 3})
        if res <= 0:
            return

        segm_len = len(self.buf) - 3
        print("OTA segm %d + %d" % (self.filetot, segm_len))
        self.tmpfile.write(self.buf[2:-1])
        self.filetot += segm_len

        self.buf =  b''
        gc.collect()

        if self.filetot > self.filelen:
            print("OTA recv file too long")
            self.sm.schedule_trans_now("connlost")
            return

        try:
            self.connection.send(b'2')
        except sockerror as e:
            print("Failure while acking payload")
            self.sm.schedule_trans_now("connlost")
            return

        if segm_len == 0:
            self.sm.schedule_trans_now("eof")

    def on_eof(self):
        self.tmpfile.close()
        self.tmpfile = None

        try:
            os.rename(self.tmpfilename, self.uplfilename)
        except OSError as e:
            print("Could not rename tmpfile onto uplfile")
            self.sm.schedule_trans_now("connlost")
            return

        try:
            self.connection.send(b'3')
        except OSError as e: # pragma: no cover
            pass

        self.sm.schedule_trans_now("done")

    def on_done(self):
        self.sm.schedule_trans_now("listen")

    def commit(self):
        res = ""
        upl = [ f for f in os.listdir(root) if f.endswith(".upl") ]
        for uplfile in upl:
            finalfile = self.decodeuplfile(uplfile)

            path_segments = finalfile.split('/')[:-1]
            path = root
            for segm in path_segments:
                path += '/' + segm
                try:
                    os.mkdir(path)
                    print('mkdir', path)
                except OSError as e:
                    # Most probably existing folder
                    pass

            try:
                print("Renaming", uplfile, finalfile)
                os.rename(uplfile, finalfile)
                res += "good " + uplfile + " -> " + finalfile + "\n"
            except OSError as e:
                res += "err " + uplfile + " -> " + finalfile + "\n"

        if not res:
            res = "nop"
        return res


singleton = None

def start():
    global singleton
    if not singleton:
        singleton = OTAHandler()

def commit():
    global singleton
    if not singleton:
        return "OTA inactive"
    return singleton.commit()
