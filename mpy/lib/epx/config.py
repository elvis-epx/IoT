import machine

class Config:
    def __init__(self):
        fname = "config.txt"

        self.data = {}

        for line in open(fname).readlines():
            items = [ x.strip() for x in line.strip().split(" ") ]
            if len(items) != 2:
                continue
            if items[1] == "None":
                items[1] = None
            self.data[items[0]] = items[1]
