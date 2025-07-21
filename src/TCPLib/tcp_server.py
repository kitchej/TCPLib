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
from typing import Generator

from .client_processor import ClientProcessor
from .tcp_client import TCPClient
from .message import Message
from .utils import vet_address

logger = logging.getLogger(__name__)


class TCPServer:
    """
    Creates, maintains, and transmits data to multiple TCP/IP connections.
    """

    def __init__(self, max_clients: int = 0, timeout: int = None):
        self._addr = None
        self._max_clients = max_clients
        self._timeout = timeout
        self._messages = queue.Queue()
        self._soc = None
        self._is_running = False
        self._is_running_lock = threading.Lock()
        self._connected_clients = {}
        self._connected_clients_lock = threading.Lock()

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

    def _get_client(self, client_id: str) -> ClientProcessor | None:
        with self._connected_clients_lock:
            try:
                client = self._connected_clients[client_id]
            except KeyError:
                return
            return client

    def _update_connected_clients(self, client_id: str, client: ClientProcessor):
        with self._connected_clients_lock:
            self._connected_clients.update({client_id: client})

    def _mainloop(self):
        logger.debug("Server is listening for connections")
        self._set_is_running(True)
        while self.is_running:
            client_soc, client_addr = None, None
            try:
                client_soc, client_addr = self._soc.accept()
                if self.is_full:
                    logger.warning("%s @ %d was denied connection due to server being full",
                                   client_addr[0], client_addr[1])
                    client_soc.close()
                    continue
                self._start_client_proc(self._generate_client_id(), client_soc)
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
            except AttributeError:  # Socket was closed from another thread
                self.stop()
                break
            except OSError:
                logger.exception("OSError raised while listening for connections")
                self.stop()
                break

        logger.debug("Server is no longer listening for messages")

    def _start_client_proc(self, client_id: str, client_soc: socket.socket):
        client = TCPClient.from_socket(client_soc)
        if not self.on_connect(client, client_id):
            client.disconnect()
            return
        client_proc = ClientProcessor(client_id=client_id,
                                      client_soc=client_soc,
                                      msg_q=self._messages,
                                      timeout=self._timeout,
                                      on_disconnect=partial(self.disconnect_client, client_id))
        client_proc.start()
        self._update_connected_clients(client_proc.id, client_proc)

    def _set_is_running(self, value: bool):
        with self._is_running_lock:
            self._is_running = value

    def on_connect(self, client: TCPClient, client_id: str):
        """
        Override to control what actions the server will take when a new client connects.
        Returning False will disconnect the client.
        """
        return True

    @property
    def addr(self) -> tuple[str, int]:
        """
        Returns a tuple with the current address the server is listening on.
        """
        return self._addr

    @property
    def is_running(self) -> bool:
        """
        Returns a boolean indicating whether the server is set up and running
        """
        with self._is_running_lock:
            return self._is_running

    @property
    def max_clients(self) -> int:
        """
        Returns an int representing the maximum allowed connections. Zero indicates that the server will allow infinite
        connections.
        """
        return self._max_clients

    @max_clients.setter
    def max_clients(self, new_max: int):
        """
        Sets the maximum number of allowed connections. The new_max argument should be a positive integer. Setting to
        zero will allow infinite connections.
        """
        if new_max < 0:
            raise ValueError("Value for max_clients should be a positive integer")
        self._max_clients = new_max

    @property
    def timeout(self) -> int | float | None:
        """
        Returns the timeout of the server's socket object used for listening for new connections
        """
        return self._timeout

    @timeout.setter
    def timeout(self, timeout: int | float | None):
        """
        Sets timeout (in seconds) of the server's socket object used for listening for new connections. The Timeout
        argument should be a positive integer. Passing None will set the timeout to infinity. See
        https://docs.python.org/3/library/socket.html#socket-timeouts for more information about timeouts.
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
        Returns and int representing the number of connected clients
        """
        with self._connected_clients_lock:
            return len(self._connected_clients.keys())

    @property
    def is_full(self) -> bool:
        """
        Returns boolean flag indicating if the server is full
        """
        if self._max_clients > 0:
            if self.client_count == self._max_clients:
                return True
        return False

    def set_clients_timeout(self, timeout: int):
        """
        Sets the timeout (in seconds) of the all current client sockets. The Timeout argument should be a positive
        integer. Passing None will set the timeout to infinity. Returns True on success, False if not.
        See https://docs.python.org/3/library/socket.html#socket-timeouts for more information about timeouts.
        """
        if timeout < 0:
            raise ValueError("Timeout cannot be less than zero")
        for client_id in self.list_clients():
            client_proc = self._get_client(client_id)
            client_proc.timeout = timeout

    def list_clients(self) -> list:
        """
        Returns a list with the client ids of all connected clients
        """
        with self._connected_clients_lock:
            return list(self._connected_clients.keys())

    def get_client_info(self, client_id: str) -> dict:
        """
        Gives basic info about a client given a client_id.
        Returns a dictionary with keys 'is_running', 'timeout', 'addr'.
        Returns an empty dictionary if a client with client_id cannot be found
        """
        client = self._get_client(client_id)
        if not client:
            return {}
        return {
            "is_running": client.is_running,
            "timeout": client.timeout,
            "addr": client.remote_addr,
        }

    def disconnect_client(self, client_id: str) -> bool:
        """
        Disconnects a client with client_id. Returns False if no client with client_id was connected,
        True on a successful disconnect.
        """
        with self._connected_clients_lock:
            try:
                client = self._connected_clients[client_id]
            except KeyError:
                return False
            del self._connected_clients[client_id]

        if client.is_running:
            client.stop(suppress_callback=True)
        logger.info("Client %s has been disconnected.", client_id)
        return True

    def pop_msg(self, block: bool = False, timeout: int = None) -> Message | None:
        """
        Get the next message in the queue. If block is 'True', this method will block until it can pop something from
        the queue, else it will try to get a value and return 'None' if queue is empty. If block is 'True' and a timeout
        is given, block until timeout expires and then return 'None' if no item was received.
        See  https://docs.python.org/3/library/queue.html#queue.Queue.get for more information
        """
        try:
            return self._messages.get(block=block, timeout=timeout)
        except queue.Empty:
            return

    def get_all_msg(self, block: bool = False, timeout: int = None) -> Generator:
        """
        Generator for iterating over the message queue. If block is 'True', each iteration of this method will block until it
        can pop something from the queue, else it will try to get a value and yield 'None' if queue is empty. If block
        is 'True' and a timeout is given, block until timeout expires and then yield 'None' if no item was received. See
        https://docs.python.org/3/library/queue.html#queue.Queue.get for more information.
        """
        while not self._messages.empty():
            yield self.pop_msg(block=block, timeout=timeout)

    def has_messages(self) -> bool:
        """
        Returns a boolean indicating if the message queue has any messages
        """
        return not self._messages.empty()

    def send(self, client_id: str, data: bytes) -> bool:
        """
        Sends data to a connected client. Returns 'True' on successful sending, 'False' if not or if a client with
        client_id could not be found.
        """
        with self._connected_clients_lock:
            try:
                client = self._connected_clients[client_id]
            except KeyError:
                return False
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
        Stops the server. If the server is not running, this method will do nothing.
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
