"""
client_processor.py
Written by: Joshua Kitchen - 2024
"""

import logging
import socket
import threading
import queue
from functools import partial

from .message import Message
from .tcp_client import TCPClient

logger = logging.getLogger(__name__)


class ClientProcessor:
    """
    Maintains a single TCP client connection.
    Pass a callback to on_disconnect to enable certain actions to be taken when stop() is called.
    """

    def __init__(self, client_id,
                 client_soc: socket.socket,
                 msg_q: queue.Queue,
                 buff_size=4096,
                 timeout: int | None = None,
                 max_timeouts: int = None,
                 on_disconnect: partial | None = None):
        self._client_id = client_id
        self._tcp_client = TCPClient.from_socket(client_soc, is_component=True)
        self._tcp_client.timeout = timeout
        self._remote_addr = client_soc.getpeername()
        self._msg_q = msg_q
        self._buff_size = buff_size
        self._is_running = False
        self._thread = None
        self._is_running_lock = threading.Lock()
        self._max_timeouts = max_timeouts
        self._total_timeouts = 0
        self._total_timeouts_lock = threading.Lock()
        self._on_disconnect = on_disconnect

    def __repr__(self):
        return f"<ClientProcessor remote_addr={self._remote_addr} running={self.is_running} client_id={self._client_id}>"

    def _receive_loop(self):
        """Listens for incoming messages from the client connection being managed. Runs on a background thread."""
        logger.debug("Client %s has started _receive_loop() and is listening for new messages from %s @ %d",
                     self._client_id, self.remote_addr[0], self.remote_addr[1])
        self._set_is_running(True)
        while self.is_running:
            try:
                data = self._tcp_client.receive(self._buff_size, suppress_logs=True)
            except TimeoutError:
                logger.warning("Timed out while receiving from %s @ %d", self.remote_addr[0], self.remote_addr[1])
                with self._total_timeouts_lock:
                    self._total_timeouts += 1
                    if self._max_timeouts is not None:
                        if self._total_timeouts >= self._max_timeouts:
                            logger.warning("Client %s timed out too many times. Disconnecting.", self._client_id)
                            self.stop()
                            return
                continue
            except ConnectionError:
                logger.debug("Receive loop for client #%s on %s @ %d was interrupted", self._client_id, self.remote_addr[0],
                             self.remote_addr[1])
                self.stop()
                return
            except OSError:
                logger.exception("OS error while receiving from %s @ %d", self.remote_addr[0],
                                 self.remote_addr[1])
                self.stop()
                return

            if len(data) == 0:
                logger.exception("Empty data from %s @ %d, disconnecting", self.remote_addr[0],
                                 self.remote_addr[1])
                self.stop()
                return

            with self._total_timeouts_lock:
                self._total_timeouts = 0
            self._msg_q.put(Message(len(data), data, self._client_id))

    def _set_is_running(self, new_value):
        """A thread-safe way of setting the _is_running state of the class"""
        with self._is_running_lock:
            self._is_running = new_value

    @property
    def id(self) -> str:
        """
        Returns a string indicating the id of the client.
        """
        return self._client_id

    @property
    def timeout(self) -> int | float | None:
        """
        Returns an int representing the current timeout value.
        """
        return self._tcp_client.timeout

    @timeout.setter
    def timeout(self, timeout: int | float | None):
        """
        Sets how long the client will wait for messages from the server (in seconds). The Timeout argument should be
        a positive integer. Setting to zero will cause network operations to fail if no data is received immediately.
        Passing 'None' will set the timeout to infinity. Returns 'True' on success, 'False' if not. See
        https://docs.python.org/3/library/socket.html#socket-timeouts for more information about timeouts.
        """
        self._tcp_client.timeout = timeout

    @property
    def total_timeouts(self) -> int | None:
        """
        Returns an integer representing the number of times the client connection has timed out.
        """
        with self._total_timeouts_lock:
            return self._total_timeouts

    @property
    def max_timeouts(self) -> int | None:
        """
        Returns an integer representing the max amount of times the client connection will time out before
        disconnecting. A value of 'None' represents infinite timeouts. A zero means that the connection can only
        time out once before disconnecting.
        """
        with self._total_timeouts_lock:
            return self._max_timeouts

    @max_timeouts.setter
    def max_timeouts(self, value: int | None):
        """
        Sets the max amount of times the internal receive loop will time out before disconnecting.
        A value of 'None' represents infinite timeouts. A zero means that the connection can only
        time out once before disconnecting.
        """
        with self._total_timeouts_lock:
            self._max_timeouts = value

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
        if not self.is_running:
            logger.warning("Attempted to send on inactive ClientProcessor %s", self._client_id)
            return False
        return self._tcp_client.send(data)

    def start(self):
        """
        Starts the client processor. If the processor is already running, this method does nothing.
        """
        if self.is_running:
            return

        if self._thread is None:
            self._thread = threading.Thread(target=self._receive_loop,
                                            daemon=True,
                                            name=f"TCPServerClientProc#{self._client_id}")
            self._thread.start()
            logger.info("Processing connection to %s @ %d as client #%s", self.remote_addr[0],
                        self.remote_addr[1], self._client_id)

    def stop(self, suppress_callback=False):
        """
        Stops the client processor. If the processor is not running, this method does nothing.
        If suppress_callback=True, it will disable the on_disconnect callback. This can help prevent deadlocks in cases
        where the same lock needs to be acquired by both the caller and the callback.
        """
        if self.is_running:
            self._set_is_running(False)
            if self._thread:
                try:
                    self._thread.join(timeout=1)  # Wait for _receive_loop to quit on its own...
                except RuntimeError:  # ...unless it already did
                    pass
            self._tcp_client.disconnect()
            self._msg_q.put(Message(0, bytes(), self._client_id))
            if self._on_disconnect is not None and not suppress_callback:
                try:
                    self._on_disconnect()
                except KeyError: # The client may be already disconnected before _on_disconnect() is called. However
                    pass         # we don't care about the KeyError raised by TCPServer.disconnect_client() because we
                                 # we're going to disconnect anyway.
