import machine, os

class NVS:
    def __init__(self, namespace):
        self.namespace = namespace

    def _read(self, kind, key):
        fname = "nvram_%s_%s_%s.sim" % (kind, self.namespace, key)
        try:
            return open(fname, "rb").read()
        except FileNotFoundError:
            return None

    def _write(self, kind, key, value):
        fname = "nvram_%s_%s_%s.sim" % (kind, self.namespace, key)
        open(fname, "wb").write(value)

    def set_i32(self, key, value):
        self._write("i", key, b"%d" % value)

    def get_i32(self, key):
        blob = self._read("i", key)
        if blob is None:
            raise OSError("key not found")
        try:
            return int(blob)
        except ValueError:
            raise OSError("key not found II")

    def set_blob(self, key, value):
        self._write("b", key, value)

    def get_blob(self, key, buffer):
        blob = self._read("b", key)
        if blob is None:
            raise OSError("key not found")
        if len(blob) > len(buffer):
            raise OSError("blob too big")
        for i in range(0, len(blob)):
            buffer[i] = blob[i]
        return len(blob)

    def commit(self):
        pass

class Partition:
    TYPE_APP = 1
    RUNNING = 2

    def __init__(self, partition_type, name=None):
        self.partition_type = partition_type
        if partition_type == self.RUNNING:
            name = "ota_0"
        self.name = name
        self.output = None

    def info(self):
        return (None, None, None, None, self.name)

    def get_next_update(self):
        if os.path.exists("noota.sim"):
            raise OSError("no OTA support")
        return Partition(self.TYPE_APP, "ota_1")

    def writeblocks(self, blkno, payload):
        if not self.output:
            self.output = open("fwupload.sim", "wb")
            self.blk = 0
        assert(blkno == self.blk)
        assert(len(payload) == 4096)
        self.output.write(payload)
        self.blk += 1

    def set_boot(self):
        self.output.close()
        self.output = None
        pass

    @staticmethod
    def mark_app_valid_cancel_rollback():
        pass

    @staticmethod
    def find(partition_type):
        return [Partition(Partition.TYPE_APP, "ota_0"), Partition(Partition.TYPE_APP, "ota_1")]
