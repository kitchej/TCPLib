import threading
import time
import socket


class ConfigurableClient:
    def __init__(self, host, port):
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host_addr = (host, port)

    def send(self, data: bytes):
        self.soc.sendall(data)

    def connect(self):
        self.soc.connect(self.host_addr)

    def close(self):
        if self.soc is not None:
            self.soc.close()
            self.soc = None


class DummyServer(ConfigurableClient):
    def __init__(self, host, port):
        ConfigurableClient.__init__(self, host, port)
        self.soc = None
        self.listen_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_soc.bind((host, port))

    def listen(self, delay):
        try:
            self.listen_soc.listen()
            time.sleep(delay)
            self.soc, _ = self.listen_soc.accept()
            self.listen_soc.close()
        except OSError:
            return

    def start(self, delay=0):
        threading.Thread(target=self.listen, args=[delay]).start()
        time.sleep(0.1)

    def stop(self):
        if self.listen_soc:
            self.listen_soc.close()
        if self.soc:
            self.soc.close()


class SocRaiseErr(socket.socket):
    """
    Socket object that raises a specific exception during operation
    param:
        - excep = Exception to be raised
        - func_to_fail = Method to raise exception in
            Valid values are:
            - accept
            - listen
            - connect
            - sendall
            - recv
    """

    def __init__(self, *args, **kwargs):
        try:
            self.excep = kwargs['excep']
            del kwargs['excep']
        except KeyError:
            self.excep = None
        try:
            self.func_to_fail = kwargs['func_to_fail']
            del kwargs['func_to_fail']
        except KeyError:
            self.func_to_fail = None
        super().__init__(*args, **kwargs)

    def listen(self, backlog=..., /):
        if self.func_to_fail == 'listen':
            if self.excep:
                raise self.excep
        if backlog is ...:
            backlog = 0
        super().listen(backlog)

    def accept(self):
        if self.func_to_fail == 'accept':
            if self.excep:
                raise self.excep
        super().accept()

    def connect(self, address, /):
        if self.func_to_fail == 'connect':
            if self.excep:
                raise self.excep
        super().connect(address)

    def sendall(self, data, flags=..., /):
        if self.func_to_fail == 'sendall':
            if self.excep:
                raise self.excep
        if flags is ...:
            flags = 0
        super().sendall(data, flags)

    def recv(self, bufsize, flags=..., /):
        if self.func_to_fail == 'recv':
            if self.excep:
                raise self.excep
        if flags is ...:
            flags = 0
        super().recv(bufsize, flags)
