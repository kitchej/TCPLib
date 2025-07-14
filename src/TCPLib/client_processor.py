"""
client_processor.py
Written by: Joshua Kitchen - 2024
"""

import logging
import socket
import threading
import queue

from .message import Message
from .tcp_client import TCPClient

logger = logging.getLogger(__name__)


class ClientProcessor:
    """
    Maintains a single TCP/IP client connection.
    """

    def __init__(self, client_id, client_soc: socket.socket, msg_q: queue.Queue, buff_size=4096, timeout: int | None = None):
        self._client_id = client_id
        self._tcp_client = TCPClient.from_socket(client_soc)
        self._tcp_client.timeout = timeout
        self._remote_addr = client_soc.getpeername()
        self._msg_q = msg_q
        self._buff_size = buff_size
        self._is_running = False
        self._thread = None
        self._is_running_lock = threading.Lock()

    def _receive_loop(self):
        logger.debug("Client %s is listening for new messages from %s @ %d",
                     self._client_id, self.remote_addr[0], self.remote_addr[1])
        self._set_is_running(True)
        while self.is_running:
            try:
                data = self._tcp_client.receive(self._buff_size)
            except AttributeError: # Socket was closed from another thread
                logger.debug("Socket was closed during receive loop")
                self.stop()
                return
            except TimeoutError:
                logger.exception("Timed out while receiving from %s @ %d", self.remote_addr[0], self.remote_addr[1])
                self.stop()
                return
            except ConnectionError:
                logger.exception("Connection error while receiving from %s @ %d", self.remote_addr[0], self.remote_addr[1])
                self.stop()
                return
            except OSError:
                logger.exception("OS error while receiving from %s @ %d", self.remote_addr[0],
                                 self.remote_addr[1])
                self.stop()
                return

            if len(data) == 0:
                logger.info("Received empty data from client %s, stopping", self._client_id)
                self.stop()
                return

            self._msg_q.put(Message(len(data), data, self._client_id))

    def _set_is_running(self, new_value):
        with self._is_running_lock:
            self._is_running = new_value


    @property
    def id(self) -> str:
        """
        Returns a string indicating the id of the client.
        """
        return self._client_id


    @property
    def timeout(self) -> int | None:
        """
        Returns an int representing the current timeout value.
        """
        return self._tcp_client.timeout

    @timeout.setter
    def timeout(self, timeout: int):
        """
        Sets how long the client will wait for messages from the server (in seconds). The Timeout argument should be
        a positive integer. Setting to zero will cause network operations to fail if no data is received immediately.
        Passing 'None' will set the timeout to infinity. Returns True on success, False if not. See
        https://docs.python.org/3/library/socket.html#socket-timeouts for more information about timeouts.
        """
        self._tcp_client.timeout = timeout

    @property
    def remote_addr(self) -> tuple[str, int]:
        """
        Returns a tuple with the client's ip (str) and the port (int)
        """
        return self._remote_addr

    @property
    def is_running(self) -> bool:
        """
        Returns a boolean indicating whether the client processor is set up and running
        """
        with self._is_running_lock:
            return self._is_running

    def send(self, data: bytes) -> bool:
        """
        Send bytes to the client with a 4 byte header attached. Returns True on successful transmission,
        False on failed transmission. Raises TimeoutError, ConnectionError, and OSError.
        """
        return self._tcp_client.send(data)

    def start(self):
        """
        Starts the client processor. If the processor is already running, this method does nothing.
        """
        if self.is_running:
            return

        if self._thread is None:
            self._thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._thread.start()
            logger.info("Processing connection to %s @ %d as client #%s", self.remote_addr[0],
                    self.remote_addr[1], self._client_id)

    def stop(self):
        """
        Stops the client processor. If the processor is not running, this method does nothing.
        """
        if self.is_running:
            self._set_is_running(False)
            if self._thread:
                self._thread.join(timeout=1) # Wait for _receive_loop to quit on its own
            self._tcp_client.disconnect()
            logger.info("Client %s has been stopped.", self._client_id)
