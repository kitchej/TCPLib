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
    Maintains a single client connection for the server.
    """

    def __init__(self, client_id, client_soc: socket.socket, msg_q: queue.Queue, server_obj,
                 buff_size=4096, timeout: int = None):
        self._client_id = client_id
        self._tcp_client = TCPClient.from_socket(client_soc)
        self._tcp_client.set_timeout(timeout)
        self._msg_q = msg_q
        self._server_obj = server_obj
        self._buff_size = buff_size
        self._is_running = True
        th = threading.Thread(target=self._receive_loop)
        th.start()
        logger.info(f"Processing %s @ %d as client #%s", self.addr()[0], self.addr()[1], self._client_id)

    def _receive_loop(self):
        logger.debug("Client %s is listening for new messages from %s @ %d",
                     self._client_id, self.addr()[0], self.addr()[1])
        while self._is_running:
            try:
                msg = self._tcp_client.receive_all(self._buff_size)
            except ConnectionError as e:
                logger.debug("Exception while receiving from %s @ %d", self._tcp_client.addr()[0],
                             self._tcp_client.addr()[1], exc_info=e)
                self.stop()
                self._msg_q.put(Message(0, None, self._client_id))
                return
            except OSError as e:
                logger.debug("Exception while receiving from %s @ %d", self._tcp_client.addr()[0],
                             self._tcp_client.addr()[1], exc_info=e)
                self.stop()
                self._msg_q.put(Message(0, None, self._client_id))
                return

            msg.client_id = self._client_id
            if msg.data is None:
                continue
            self._msg_q.put(msg)

    def id(self) -> str:
        """
        Returns a string indicating the id of the client.
        """
        return self._client_id

    def timeout(self) -> int:
        """
        Returns an int representing the current timeout value.
        """
        return self._tcp_client.timeout()

    def set_timeout(self, timeout: int) -> bool:
        """
        Sets how long the client will wait for messages from the server (in seconds). The Timeout argument should be
        a positive integer. Setting to zero will cause network operations to fail if no data is received immediately.
        Passing 'None' will set the timeout to infinity. Returns True on success, False if not. See
        https://docs.python.org/3/library/socket.html#socket-timeouts for more information about timeouts.
        """
        return self._tcp_client.set_timeout(timeout)

    def send(self, data: bytes) -> bool:
        """
        Send all bytes of the data argument with a header attached. Returns True on successful transmission,
        False on failed transmission. Raises TimeoutError, ConnectionError, socket.gaierror, and OSError.
        """
        return self._tcp_client.send(data)

    def addr(self) -> tuple[str, int]:
        """
        Returns a tuple with the host's ip (str) and the port (int)
        """
        return self._tcp_client.addr()

    def set_addr(self, host: str, port: int):
        """
        Allows for the address to be changed after class creation. If the server is running, this function will do
        nothing.
        """
        self._tcp_client.set_addr(host, port)

    def is_running(self):
        """
        Returns a boolean indicating whether the client processor is set up and running
        """
        return self._is_running

    def stop(self):
        """
        Stops the client processor. If the client is not running, this method will do nothing.
        """
        if self._is_running:
            self._is_running = False
            self._tcp_client.disconnect()
            logger.info(f"Client %s has been stopped.", self._client_id)
