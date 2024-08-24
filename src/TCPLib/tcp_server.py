"""
tcp_server.py
Written by: Joshua Kitchen - 2024

TODO:
    - Better system for controlling the timeout of the server and all its client connections
"""
import logging
import socket
import threading
import queue
import random

from .internals.client_processor import ClientProcessor
from .internals.utils import encode_msg

logger = logging.getLogger(__name__)


class TCPServer:
    '''Class for creating, maintaining, and transmitting data to multiple client connections.'''

    def __init__(self, host: str, port: int, max_clients: int = 0, timeout: int = None):
        self._max_clients = max_clients
        self._connected_clients = {}
        self._connected_clients_lock = threading.Lock()
        self._messages = queue.Queue()
        self._is_running = False
        self._timeout = timeout
        self._addr = (host, port)
        self._soc = None

    @staticmethod
    def _generate_client_id():
        client_id = str(random.randint(0, 999999))
        client_id = int(client_id, base=36)
        return str(client_id)

    def _get_client(self, client_id: str):
        self._connected_clients_lock.acquire()
        try:
            client = self._connected_clients[client_id]
        except KeyError:
            self._connected_clients_lock.release()
            return
        self._connected_clients_lock.release()
        return client

    def _update_connected_clients(self, client_id: str, client: ClientProcessor):
        self._connected_clients_lock.acquire()
        self._connected_clients.update({client_id: client})
        self._connected_clients_lock.release()

    def _create_soc(self):
        self._soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._soc.settimeout(self._timeout)
        try:
            self._soc.bind(self._addr)
        except socket.gaierror:
            logger.exception(f"Exception when trying to bind to %s @ %d", self._addr[0], self._addr[1])
            return False
        return True

    def _mainloop(self):
        while self.is_running():
            try:
                self._soc.listen()
                client_soc, client_addr = self._soc.accept()
                logger.info("Accepted Connection from %s @ %d", client_addr[0], client_addr[1])
                if self.is_full():
                    logger.debug("%s @ %d was denied connection due to server being full",
                                 client_addr[0], client_addr[1])
                    client_soc.sendall(encode_msg(b'SERVER FULL', 4))  # Warn client they are being disconnected
                    client_soc.close()
                    continue
                client_soc.sendall(encode_msg(b'0', 2))
                self.start_client_proc(self._generate_client_id(),
                                       client_addr[0],
                                       client_addr[1],
                                       client_soc)
            except OSError:
                logger.exception(f"Exception occurred while listening on %s @ %d", self._addr[0], self._addr[1])
                break

    def _on_connect(self, *args, **kwargs):
        '''
        Overridable method that runs once the client is connected. Returning false from this method will
        disconnect the client and abort client setup.
        '''
        pass

    def start_client_proc(self, client_id: str, host: str, port: int, client_soc: socket.socket):
        result = self._on_connect(client_soc, client_id, host, port)
        if result is False:
            client_soc.close()
            return
        client_proc = ClientProcessor(client_id=client_id,
                                      host=host,
                                      port=port,
                                      client_soc=client_soc,
                                      msg_queue=self._messages,
                                      server_obj=self,
                                      timeout=self._timeout)

        client_proc.start()
        self._update_connected_clients(client_proc.id(), client_proc)

    def addr(self):
        return self._addr

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
        if new_max < 0:
            return False
        self._max_clients = new_max
        return True

    def set_timeout(self, timeout: int):
        if timeout is None:
            pass
        elif timeout < 0:
            return False
        self._timeout = timeout

        for client_id in self.list_clients():
            client_proc = self._get_client(client_id)
            result = client_proc.set_timeout(timeout)
            if not result:
                return False
        return True

    def timeout(self):
        return self._timeout

    def list_clients(self):
        self._connected_clients_lock.acquire()
        client_list = self._connected_clients.keys()
        self._connected_clients_lock.release()
        return list(client_list)

    def get_client_info(self, client_id: str):
        client = self._get_client(client_id)
        if not client:
            return
        return {
            "is_running": client.is_running(),
            "timeout": client.timeout(),
            "host": client.addr()[0],
            "port": client.addr()[1]
        }

    def disconnect_client(self, client_id: str, warn: bool = True):
        self._connected_clients_lock.acquire()
        try:
            client = self._connected_clients[client_id]
        except KeyError:
            self._connected_clients_lock.release()
            return False
        del self._connected_clients[client_id]
        self._connected_clients_lock.release()
        if client.is_running():
            client.stop(warn=warn)
        return True

    def pop_msg(self, block: bool = False, timeout: int = None):
        try:
            return self._messages.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def get_all_msg(self, block: bool = False, timeout: int = None):
        while not self._messages.empty():
            yield self.pop_msg(block=block, timeout=timeout)

    def has_messages(self):
        return not self._messages.empty()

    def send(self, client_id: str, data: bytes):
        self._connected_clients_lock.acquire()
        try:
            client = self._connected_clients[client_id]
        except KeyError:
            self._connected_clients_lock.release()
            return False
        self._connected_clients_lock.release()
        return client.send(data, 2)

    def start(self):
        if self._is_running:
            return False
        if not self._create_soc():
            return False
        self._is_running = True
        threading.Thread(target=self._mainloop).start()
        logger.info("Server has been started")
        return True

    def stop(self):
        if self._is_running:
            self._connected_clients_lock.acquire()
            for client in self._connected_clients.values():
                client.stop()
            self._connected_clients.clear()
            self._connected_clients_lock.release()
            self._soc.close()
            self._soc = None
            self._is_running = False
            logger.info("Server has been stopped")
