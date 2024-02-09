import logging
import threading
import queue

from internals.listener import Listener
from internals.client_processor import ClientProcessor

# Bindings for log levels, so the user doesn't have to import the logging module for one parameter

INFO = logging.INFO
DEBUG = logging.DEBUG


class TCPServer:
    def __init__(self, host, port, max_clients=0, buff_size=4096, logging_level=INFO, log_path=".server_log.txt"):
        self._max_clients = max_clients
        self._buff_size = buff_size
        self._connected_clients = {}
        self._connected_clients_lock = threading.Lock()
        self._messages = queue
        self._is_running = False
        self._listener = Listener(host, port, self)

        logging.basicConfig(filename=log_path, filemode='w', level=logging_level,
                            format="%(asctime)s - %(levelname)s: %(message)s",
                            datefmt="%m/%d/%Y %I:%M:%S %p")

    def update_connected_clients(self, client_id: str, client: ClientProcessor):
        pass

    def addr(self):
        return self._listener.addr()

    def is_running(self):
        return self._is_running

    def client_count(self):
        self._connected_clients_lock.acquire()
        count = len(self._connected_clients.keys())
        self._connected_clients_lock.release()
        return count

    def is_full(self):
        if self._max_clients > 0:
            if self.client_count() == self._max_clients:
                return True
        return False

    def max_clients(self):
        return self._max_clients

    def set_max_clients(self, new_max: int):
        self._max_clients = new_max

    def list_clients(self):
        pass

    def disconnect_client(self, client_id: str):
        pass

    def pop_msg(self):
        pass

    def get_all_msg(self):
        pass

    def send_msg(self, client_id: str, data: bytes):
        pass
