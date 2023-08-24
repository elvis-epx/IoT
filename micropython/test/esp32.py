import machine

class NVS:
    def __init__(self, namespace):
        self.namespace = namespace

    def _read(self, kind, key):
        fname = "%s/nvram_%s_%s_%s.key" % (machine.TEST_FOLDER, kind, self.namespace, key)
        try:
            return open(fname).read()
        except FileNotFoundError:
            return None

    def _write(self, kind, key, value):
        fname = "%s/nvram_%s_%s_%s.key" % (machine.TEST_FOLDER, kind, self.namespace, key)
        open(fname, "wb").write(value)

    def set_i32(self, key, value):
        self._write("i", key, b"%d" % value)

    def get_i32(self, key):
        blob = self._read("b", key)
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
