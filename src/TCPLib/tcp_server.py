"""
tcp_server.py
Written by: Joshua Kitchen - 2024
"""
import logging
import socket
import threading
import queue
import random
from typing import Generator

from .internals.client_processor import ClientProcessor
from .internals.utils import encode_msg
from .message import Message

logger = logging.getLogger(__name__)


class TCPServer:
    """
    Class for creating, maintaining, and transmitting data to multiple client connections. This class can
    accept and use an external Queue object
    """
    def __init__(self, host: str = None, port: int = None, max_clients: int = 0, timeout: int = None,
                 msg_q: queue.Queue = None):
        self._max_clients = max_clients
        self._connected_clients = {}
        self._connected_clients_lock = threading.Lock()
        self._is_running = False
        self._timeout = timeout
        self._addr = (host, port)
        self._soc = None
        if msg_q:
            self._messages = msg_q
        else:
            self._messages = queue.Queue()

    @staticmethod
    def _generate_client_id() -> str:
        client_id = str(random.randint(0, 999999))
        client_id = int(client_id, base=36)
        return str(client_id)

    def _get_client(self, client_id: str) -> ClientProcessor | None:
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

    def _create_soc(self) -> bool:
        self._soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
                    client_soc.sendall(encode_msg(b'SERVER FULL'))
                    client_soc.close()
                    continue
                client_soc.sendall(encode_msg(b'CONNECTION ACCEPTED'))
                self._start_client_proc(self._generate_client_id(),
                                        client_addr[0],
                                        client_addr[1],
                                        client_soc)
            except OSError:
                logger.exception(f"Exception occurred while listening on %s @ %d", self._addr[0], self._addr[1])
                break

    def _on_connect(self, *args, **kwargs):
        """
        Overridable method that runs once the client is connected. Returning 'False' from this method will
        disconnect the client and abort client setup.
        """
        pass

    def _start_client_proc(self, client_id: str, host: str, port: int, client_soc: socket.socket):
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

    def addr(self) -> tuple[str, int]:
        """
        Returns a tuple with the current ip (str) and the port (int) the server is listening on.
        """
        return self._addr

    def set_addr(self, host: str, port: int):
        """
        Allows for the address to be changed after class creation. If the server is running, this function will do
        nothing.
        """
        if self._is_running:
            return
        self._addr = (host, port)

    def is_running(self) -> bool:
        """
        Returns a boolean indicating whether the server is set up and running
        """
        return self._is_running

    def client_count(self) -> int:
        """
        Returns and int representing the number of connected clients
        """
        self._connected_clients_lock.acquire()
        count = len(self._connected_clients.keys())
        self._connected_clients_lock.release()
        return count

    def is_full(self) -> bool:
        """
        Returns boolean flag indicating if the server is full
        """
        if self._max_clients > 0:
            if self.client_count() == self._max_clients:
                return True
        return False

    def max_clients(self) -> int:
        """
        Returns an int representing the maximum allowed connections. Zero indicates that the server will allow infinite
        connections.
        """
        return self._max_clients

    def set_max_clients(self, new_max: int) -> bool:
        """
        Sets the maximum number of allowed connections. The new_max argument should be a positive integer. Setting to
        zero will allow infinite connections. Returns True on success, False if not.
        """
        if new_max < 0:
            return False
        self._max_clients = new_max
        return True

    def set_clients_timeout(self, timeout: int) -> bool:
        """
        Sets the timeout (in seconds) of the all current client sockets. The Timeout argument should be a positive
        integer. Passing None will set the timeout to infinity. Returns True on success, False if not.
        See https://docs.python.org/3/library/socket.html#socket-timeouts for more information about timeouts.
        """
        if timeout is None:
            pass
        elif timeout < 0:
            return False
        for client_id in self.list_clients():
            client_proc = self._get_client(client_id)
            result = client_proc.set_timeout(timeout)
            if not result:
                return False
        return True

    def set_server_timeout(self, timeout: int) -> bool:
        """
        Sets timeout (in seconds) of the server's socket object used for listening for new connections. The Timeout
        argument should be a positive integer. Passing None will set the timeout to infinity. See
        https://docs.python.org/3/library/socket.html#socket-timeouts for more information about timeouts.
        """
        if timeout is None:
            pass
        elif timeout < 0:
            return False
        self._timeout = timeout
        self._soc.settimeout(timeout)
        return True

    def server_timeout(self) -> int:
        """
        Returns the timeout of the server's socket object used for listening for new connections
        """
        return self._timeout

    def list_clients(self) -> list:
        """
        Returns a list of with the client ids of all connected clients
        """
        self._connected_clients_lock.acquire()
        client_list = self._connected_clients.keys()
        self._connected_clients_lock.release()
        return list(client_list)

    def get_client_info(self, client_id: str) -> dict | None:
        """
        Gives basic info about a client given a client_id.
        Returns a dictionary with keys 'is_running', 'timeout', 'addr'.
        Returns None if a client with client_id cannot be found
        """
        client = self._get_client(client_id)
        if not client:
            return
        return {
            "is_running": client.is_running(),
            "timeout": client.timeout(),
            "addr": (client.addr()[0], client.addr()[1]),
        }

    def disconnect_client(self, client_id: str) -> bool:
        """
        Disconnects a client with client_id. Returns False if no client with client_id was connected,
        True on a successful disconnect.
        """
        self._connected_clients_lock.acquire()
        try:
            client = self._connected_clients[client_id]
        except KeyError:
            self._connected_clients_lock.release()
            return False
        del self._connected_clients[client_id]
        self._connected_clients_lock.release()
        if client.is_running():
            client.stop()
        return True

    def pop_msg(self, block: bool = False, timeout: int = None) -> Message | None:
        """
        Get the next message in the queue. If block is True, this method will block until it can pop something from
        the queue, else it will try to get a value and return None if queue is empty. If block is True and a timeout
        is given, block until timeout expires and then return None if no item was received.
        See  https://docs.python.org/3/library/queue.html#queue.Queue.get for more information
        """
        try:
            return self._messages.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def get_all_msg(self, block: bool = False, timeout: int = None) -> Generator[Message | None, None, None]:
        """
        Generator for iterating over the queue. If block is True, each iteration of this method will block until it
        can pop something from the queue, else it will try to get a value and yield None if queue is empty. If block
        is True and a timeout is given, block until timeout expires and then yield None if no item was received. See
        https://docs.python.org/3/library/queue.html#queue.Queue.get for more information
        """
        while not self._messages.empty():
            yield self.pop_msg(block=block, timeout=timeout)

    def has_messages(self) -> bool:
        """
        Returns a boolean flag indicating whether the queue has messages in it or not
        """
        return not self._messages.empty()

    def send(self, client_id: str, data: bytes) -> bool:
        """
        Sends data to a connected client. Data should be a bytes-like object. Returns True on successful sending,
        False if not or if a client with client_id could not be found.
        """
        self._connected_clients_lock.acquire()
        try:
            client = self._connected_clients[client_id]
        except KeyError:
            self._connected_clients_lock.release()
            return False
        self._connected_clients_lock.release()
        return client.send(data)

    def start(self) -> bool:
        """
        Starts the server. Returns True on successful start up, False if not.
        """
        if self._is_running:
            return False
        if not self._create_soc():
            return False
        self._is_running = True
        threading.Thread(target=self._mainloop).start()
        logger.info("Server has been started")
        return True

    def stop(self):
        """
        Stops the server. If the server is not running, this method will do nothing.
        """
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
