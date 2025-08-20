"""
tcp_server.py
Written by: Joshua Kitchen - 2024
"""
import logging
import socket
import threading
import queue
import random
import time
from functools import partial
from typing import Generator, Callable

from .client_processor import ClientProcessor
from .tcp_client import TCPClient
from .message import Message
from .utils import vet_address

logger = logging.getLogger(__name__)


class TCPServer:
    """
    Creates, maintains, and transmits data to multiple TCP connections.

    If `max_clients` is 0, the server allows an unlimited number of connections.
    If `timeout` is None, the server socket has no timeout.

    'on_connect' parameter is a callback function that will run for every new connection. Return 'False' to
    disconnect the client. Two arguments will be passed to this function: A TCPClient object and
    the client's id
    """

    def __init__(self,
                 max_clients: int = 0,
                 timeout: int | float | None = None,
                 on_connect: Callable[[TCPClient, str], bool] | None = None):
        self._addr = None
        self._max_clients = max_clients
        self._timeout = timeout
        self._messages = queue.Queue()
        self._soc = None
        self._is_running = False
        self._is_running_lock = threading.Lock()
        self._connected_clients = {}
        self._connected_clients_lock = threading.Lock()
        self._on_connect = on_connect

    def __repr__(self):
        return (f"<TCPServer addr={self._addr} "
                f"running={self.is_running} "
                f"max_clients={self.max_clients} "
                f"client_count={self.client_count}>")

    @classmethod
    def from_socket(cls, soc: socket.socket, max_clients: int = 0) -> "TCPServer":
        """
        Allows for a server to be created from a socket object. Returns a TCPServer object.
        NOTE: socket.bind() and socket.listen() are called on the socket when start() is called. If bind() or listen()
        are called on the socket BEFORE start(), an exception will be raised.
        """
        out = cls(max_clients, soc.gettimeout())
        out._soc = soc
        return out

    @staticmethod
    def _generate_client_id() -> str:
        timestamp_part = str(int(time.time() * 1000))[-9:]
        random_part = f"{random.randint(0, 999):03d}"
        return timestamp_part + random_part

    def _mainloop(self):
        """
        Mainloop of the server. Listens for connections and attaches it to a ClientProcessor
        """
        logger.debug("Server is listening for connections")
        self._set_is_running(True)
        while self.is_running:
            client_soc, client_addr = None, None
            try:
                client_soc, client_addr = self._soc.accept()
            except TimeoutError:
                if client_addr is None:
                    logger.warning("New connection timed out before connection could be accepted")
                else:
                    logger.warning("%s @ %d timed out while setting up it's client processor",
                                   client_addr[0], client_addr[1])
                continue
            except ConnectionError as e:
                if client_addr is None:
                    logger.warning("New connection was disconnected before connection could be accepted")
                else:
                    logger.warning("%s @ %d was disconnected while setting up it's client processor",
                                   client_addr[0], client_addr[1])
                continue
            except AttributeError:  # Possibly raised if the socket was closed from another thread
                self.stop()
                break
            except OSError:  # Possibly raised if the socket was closed from another thread
                if logger.getEffectiveLevel() == logging.DEBUG:
                    logger.error("OSError raised while listening for connections")
                self.stop()
                break

            if self.is_full:
                logger.warning("%s @ %d was denied connection due to server being full",
                               client_addr[0], client_addr[1])
                client_soc.close()
                continue
            self._start_client_proc(self._generate_client_id(), client_soc)

        logger.debug("Server is no longer listening for messages")

    def _start_client_proc(self, client_id: str, client_soc: socket.socket):
        """
        Contains setup necessary to start a ClientProcessor class with a new client connection and register it to
        self._connected_clients. Also calls the on_connect() callback.
        """
        client = TCPClient.from_socket(client_soc)
        if self._on_connect is not None:
            if self._on_connect(client, client_id) is False:
                client.disconnect()
                return

        client_proc = ClientProcessor(client_id=client_id,
                                      client_soc=client_soc,
                                      msg_q=self._messages,
                                      timeout=self._timeout,
                                      on_disconnect=partial(self.disconnect_client, client_id))
        client_proc.start()
        self._update_connected_clients(client_proc.id, client_proc)

    def _get_client(self, client_id: str) -> ClientProcessor:
        """
        Thread-safe way to get a connected client from self._connected_clients. Raises KeyError.
        """
        with self._connected_clients_lock:
            try:
                client = self._connected_clients[client_id]
            except KeyError: # Re-raise with more specific error message
                raise KeyError(f"Could not find a connected client with id #{client_id}")
            return client

    def _update_connected_clients(self, client_id: str, client: ClientProcessor):
        """
        Thread-safe way to add a connected client to self._connected_clients.
        """
        with self._connected_clients_lock:
            self._connected_clients.update({client_id: client})

    def _set_is_running(self, value: bool):
        """
        A thread-safe way of setting the _is_running state of the class
        """
        with self._is_running_lock:
            self._is_running = value

    @property
    def addr(self) -> tuple[str, int]:
        """
        A tuple representing the address the server is currently bound to. Read-only.
        """
        return self._addr

    @property
    def is_running(self) -> bool:
        """
        Indicates whether the server is actively listening for connections. Read-only.
        """
        with self._is_running_lock:
            return self._is_running

    @property
    def max_clients(self) -> int:
        """
        A positive integer indicating the maximum allowed client connections.  A value of 0 allows infinite connections.
        """
        return self._max_clients

    @max_clients.setter
    def max_clients(self, new_max: int):
        """
        Sets the maximum number of allowed connections. The new_max argument should be a positive integer. Setting to
        0 will allow infinite connections.
        """
        if new_max < 0:
            raise ValueError("Value for max_clients should be a positive integer")
        self._max_clients = new_max

    @property
    def timeout(self) -> int | float | None:
        """
        Timeout (in seconds) for accepting new connections. A value of `None` disables timeouts.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, timeout: int | float | None):
        """
        Sets timeout (in seconds) of the server. The Timeout argument should be a positive integer. A value of `None`
        disables timeouts.
        """
        if timeout is not None:
            if timeout < 0:
                raise ValueError("Value for timeout should be a positive integer")
        self._timeout = timeout
        if self._soc:
            self._soc.settimeout(timeout)

    @property
    def client_count(self) -> int:
        """
        The number of currently connected clients. Read-only.
        """
        with self._connected_clients_lock:
            return len(self._connected_clients.keys())

    @property
    def is_full(self) -> bool:
        """
        Boolean indicating whether the server has reached `max_clients`. Read-only.
        """
        if self._max_clients > 0:
            if self.client_count == self._max_clients:
                return True
        return False

    def set_client_attribute(self, client_id: str, attribute: str, value: any):
        """
        Set a specific attribute of a client connection. Raises KeyError if the client could not be found
        Valid attributes are:
            - 'timeout'
            - 'max_timeouts'
        """
        client_proc = self._get_client(client_id)
        if attribute == "timeout":
            client_proc.timeout = value
        elif attribute == 'max_timeouts':
            client_proc.max_timeouts = value
        elif attribute in ['is_running', 'addr', 'total_timeouts']:
            raise ValueError(f"'{attribute}' is read-only attribute")
        else:
            raise ValueError(f"'{attribute}' is an invalid attribute")

    def get_client_attributes(self, client_id: str) -> dict:
        """
        Get basic info about a client given a client_id.
        Returns a dictionary with keys 'is_running', 'timeout', 'addr', 'total_timeouts', and 'max_timeouts'.
        Raises KeyError if a client with client_id cannot be found
        """
        client = self._get_client(client_id)
        return {
            "is_running": client.is_running,
            "timeout": client.timeout,
            "addr": client.remote_addr,
            "total_timeouts": client.total_timeouts,
            "max_timeouts": client.max_timeouts
        }

    def list_clients(self) -> list:
        """
        Return a list with the client ids of all currently connected clients
        """
        with self._connected_clients_lock:
            return list(self._connected_clients.keys())

    def disconnect_client(self, client_id: str):
        """
        Disconnect a client by id. Raises `KeyError` if the client is not found.
        """
        with self._connected_clients_lock:
            try:
                client = self._connected_clients[client_id]
            except KeyError:
                raise KeyError(f"Cannot find client with id #{client_id}")
            del self._connected_clients[client_id]

        if client.is_running:
            client.stop(suppress_callback=True)
        logger.info("Client %s has been disconnected.", client_id)

    def pop_msg(self, block: bool = False, timeout: int | float | None = None) -> Message | None:
        """
        Pops the next message from the queue. If `block=True`, will block until a message is
        available. If `block=True` and a value for `timeout` is provided, block until the timeout expires.
        Returns None if the queue was empty.
        """
        try:
            return self._messages.get(block=block, timeout=timeout)
        except queue.Empty:
            return

    def get_all_msg(self) -> Generator:
        """
        A generator for iterating over the message queue. Iteration ends when the queue is empty.
        """
        while not self._messages.empty():
            yield self.pop_msg()

    def has_messages(self) -> bool:
        """
        Returns `True` if the message queue has messages.
        """
        return not self._messages.empty()

    def send(self, client_id: str, data: bytes) -> bool:
        """
        Send data to the client with `client_id`. Returns 'True' on successful sending, 'False' if not. Raises `KeyError` if
        the client could not be found.
        """
        with self._connected_clients_lock:
            try:
                client = self._connected_clients[client_id]
            except KeyError:
                raise KeyError(f"Could not find client with id #{client_id}")
            try:
                return client.send(data)
            except (ConnectionError, OSError):
                logger.warning("Failed to send to client %s", client_id)
                return False

    def start(self, addr: tuple[str, int]):
        """
        Starts the server and listens to the address provided.
        """

        if self.is_running:
            return

        if not vet_address(addr):
            raise ValueError(f"{addr} is an invalid ipv4 address")
        if addr[0] == "255.255.255.255":
            raise ValueError("Cannot connect to '255.255.255.255' (broadcast address)")

        self._addr = addr

        if not self._soc:
            self._soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._soc.bind(self._addr)
        self._soc.listen()
        threading.Thread(target=self._mainloop, daemon=True, name="TCPServerMainLoop").start()
        logger.info("Server has been started")

    def stop(self):
        """
        Disconnects all clients and shuts down the server. If the server is not running, this method will do nothing.
        """
        if self.is_running:
            with self._connected_clients_lock:
                for client in self._connected_clients.values():
                    client.stop(suppress_callback=True)
                self._connected_clients.clear()
            self._soc.close()
            self._soc = None
            self._set_is_running(False)
            self._addr = None
            logger.info("Server has been stopped")
