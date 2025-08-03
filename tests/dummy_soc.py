import logging
import threading
import time
import socket
from TCPLib.tcp_server import TCPServer

logger = logging.getLogger(__name__)

def on_connect(*args):
    return False

class DummyServer:
    def __init__(self):
        self.soc = None
        self.listen_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_ready = threading.Event()

    def listen(self):
        try:
            self.listen_soc.listen()
            self.server_ready.set()
            self.soc, _ = self.listen_soc.accept()
            self.listen_soc.close()
        except OSError:
            return

    def send(self, data: bytes):
        self.soc.sendall(data)

    def start(self, addr):
        self.listen_soc.bind(addr)
        threading.Thread(target=self.listen).start()
        self.server_ready.wait()

    def stop(self):
        if self.listen_soc:
            self.listen_soc.close()
            logger.debug("Dummy server has been closed it's listening socket")
        if self.soc:
            self.soc.close()
            logger.debug("Dummy server has been closed it's client socket")

        self.soc = None
        self.listen_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_ready = threading.Event()


class SocRaiseErr(socket.socket):
    """
    Socket object that raises a specific exception during operation
    param:
        - excep = Exception to be raised
        - func_to_fail = Method to raise exception in
            Valid values are:
            - accept
            - bind
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
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def listen(self, backlog=..., /):
        if self.func_to_fail == 'listen':
            if self.excep:
                raise self.excep
        if backlog is ...:
            backlog = 0
        return super().listen(backlog)

    def accept(self):
        if self.func_to_fail == 'accept':
            if self.excep:
                time.sleep(0.1)
                raise self.excep
        return super().accept()

    def bind(self, address, /):
        if self.func_to_fail == 'bind':
            if self.excep:
                raise self.excep
        return super().bind(address)

    def connect(self, address, /):
        if self.func_to_fail == 'connect':
            if self.excep:
                raise self.excep
        return super().connect(address)

    def sendall(self, data, flags=..., /):
        if self.func_to_fail == 'sendall':
            if self.excep:
                raise self.excep
        if flags is ...:
            flags = 0
        return super().sendall(data, flags)

    def recv(self, bufsize, flags=..., /):
        if self.func_to_fail == 'recv':
            if self.excep:
                raise self.excep
        if flags is ...:
            flags = 0
        return super().recv(bufsize, flags)
