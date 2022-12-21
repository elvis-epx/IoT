import socket
from threading import Lock
from . import Handler

class Queue(Handler):
    """
    Class to handle generic events coming from external sources, including
    from other processes or other threads. Messages are routed and delivered
    in the context of the main thread.

    Every message has a name and it is routed to a callback handler
    based on that name.
    """

    def __init__(self, name):
        self.r, self.w = socket.socketpair()
        super().__init__(name, self.r, socket.error)
        self.handlers = {}
        self.q = []
        self.qlock = Lock()

    def destroy(self):
        self.w.close()
        self.handlers = {}
        self.qlock.acquire()
        self.q = []
        self.qlock.release()
        self.qlock = None
        super().destroy()

    """
    Adds a message handler.

    Parameters:
    owner: The identification of an owner allows for multiple listeners and
           selective unsubscribing.
    name:  The message name you want to listen to.
           Different owners may listen to the same name.
           A single owner can have a single listener for one name.
    cb:    The function to be called back when message is received
    recurrent:  Whether the handler should remain active after receiving
                one message. Default is False.
    """
    def on_msg(self, owner, name, cb, recurrent=False):
        if id(owner) not in self.handlers:
            self.handlers[id(owner)] = {}
        self.handlers[id(owner)][name] = (cb, recurrent)

    """
    Adds a message handler with parsing/type conversion of contents
    Parser should raise a ValueError when value is invalid/unparsable
    """
    def on_parsed_msg(self, owner, name, cb, parser, recurrent=False):
        def closure(contents):
            try:
                value = parser(contents)
            except ValueError:
                Log.debug("Invalid message %s = '%s'" % (name, contents))
                return
            cb(value)
        self.on_msg(owner, name, closure, recurrent)

    """
    Adds a message handler with automatic conversion from string to int
    """
    def on_int(self, owner, name, cb, recurrent=False):
        self.on_parsed_msg(owner, name, cb, lambda contents: int(contents), recurrent)

    """
    Adds a message handler with automatic conversion from string to float
    """
    def on_float(self, owner, name, cb, recurrent=False):
        self.on_parsed_msg(owner, name, cb, lambda contents: float(contents), recurrent)

    """
    Removes all message handlers of a given owner.
    """
    def unobserve(self, owner):
        if id(owner) in self.handlers:
            del self.handlers[id(owner)]

    """
    Adds a message to the queue. May be called by any thread context.
    """
    def push(self, name, contents):
        self.qlock.acquire()
        self.q.append((name, contents))
        self.qlock.release()
        self.w.send(b' ')

    """
    Private method called by event loop
    """
    def read_callback(self):
        self.r.recv(1024)
        while self.q:
            self.qlock.acquire()
            msg, self.q = self.q[0], self.q[1:]
            self.qlock.release()

            name, contents = msg

            for handlers in list(self.handlers.values()):
                if name not in handlers:
                    continue
                cb, recurrent = handlers[name]
                if not recurrent:
                    del handlers[name]
                cb(contents)
