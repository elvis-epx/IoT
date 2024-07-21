import machine
if hasattr(machine, 'TEST_ENV'):
    from machine import start_new_thread
else: # pragma: no cover
    from _thread import start_new_thread
from epx.loop import Task, SECONDS
from epx import loop

class Watchdog:
    def __init__(self, config, fast_dehibernate=False):
        self.cookies = 0

        if 'watchdog' not in config.data:
            config.data['watchdog'] = "0"
        self.disabled = config.data['watchdog'] == "0"

        self.grace = (fast_dehibernate and machine.wake_reason() == machine.DEEPSLEEP) and 1 or 10

        if self.disabled:
            print("Watchdog off")
            self.grace = 0
            return

        print("Watchdog will be on in %ds" % self.grace)
        def bring_up(_):
            print("Watchdog on")
            Task(True, "watchdog", self.main_thread_feed, 1 * SECONDS)
            start_new_thread(self.wdt_thread, ())
        Task(False, "watchdog_up", bring_up, self.grace * SECONDS)

    def grace_time(self):
        return self.grace

    def main_thread_feed(self, _):
        # Called by main thread, which handles Tasks
        self.cookies = 1

    def wdt_thread(self):
        # WDT object must be created by the same thread that feeds it
        self.impl = machine.WDT(timeout=15000)

        while loop.running:
            loop.sleep(1000)
            if self.cookies > 0:
                self.impl.feed()
                self.cookies -= 1

    def may_block(self):
        # Make sure wdt_thread can feed the watchdog while
        # the main thread is blocked, but do not tolerate
        # MT blocking forever, either
        self.cookies = 120

    def may_block_exit(self):
        self.cookies = 1
