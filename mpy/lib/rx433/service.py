from epx.mqtt import MQTTPub
from epx.loop import SECONDS, MINUTES, Shortcronometer, Longcronometer


class KeyfobService(MQTTPub):
    def __init__(self, config):
        # client must call forcepub() manually
        MQTTPub.__init__(self, "stat/%s/Keyfob", 0, 0, False)
        self.value = ""

    def new_value(self, value):
        # FIXME rate limiting
        # FIXME filter repeated rx of the same value
        self.value = value
        self.forcepub()

    def gen_msg(self):
        return self.value
