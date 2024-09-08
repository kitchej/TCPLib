"""
auto_tcp_client.py
Written by: Joshua Kitchen - 2024
"""

import logging
import queue
import threading
from typing import Generator

from .message import Message
from .tcp_client import TCPClient

logger = logging.getLogger(__name__)


class AutoTCPClient:
    """
    A basic TCP client that automatically receives messages from a server and places it in a queue. This class can
    accept and use an external Queue object.
    """
    def __init__(self, host: str = None, port: int = None, client_id: str = None, msg_queue: queue.Queue = None,
                 buff_size: int = 4096, timeout: int = None):
        self._tcp_client = TCPClient(host=host, port=port, timeout=timeout)
        self._is_running = False
        self._client_id = client_id
        self._buff_size = buff_size

        if msg_queue:
            self._msg_queue = msg_queue
        else:
            self._msg_queue = queue.Queue()

    def _receive_loop(self):
        logger.debug("Client %s is listening for new messages from %s @ %d",
                     self._client_id, self.addr()[0], self.addr()[1])
        while self._is_running:
            try:
                msg = self._tcp_client.receive_all(self._buff_size)
            except ConnectionAbortedError:
                self.stop()
                return
            except ConnectionResetError:
                self.stop()
                return
            except OSError:
                logger.exception("Exception while receiving from %s @ %d", self._tcp_client.addr()[0],
                                 self._tcp_client.addr()[1])
                self.stop()
                return
            except Exception as e:
                logger.exception("Exception while receiving from %s @ %d", self._tcp_client.addr()[0],
                                 self._tcp_client.addr()[1])
                self.stop()
                raise e
            msg.client_id = self._client_id
            if msg.data is None:
                continue
            self._msg_queue.put(msg)

    def pop_msg(self, block: bool = False, timeout: int = None):
        """
        Get the next message in the queue. If block is True, this method will block until it can pop something from
        the queue, else it will try to get a value and return None if queue is empty. If block is True and a timeout
        is given, block until timeout expires and then return None if no item was received.
        See  https://docs.python.org/3/library/queue.html#queue.Queue.get for more information
        """
        try:
            return self._msg_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def get_all_msg(self, block: bool = False, timeout: int = None) -> Generator[Message | None, None, None]:
        """
        Generator for iterating over the queue. If block is True, each iteration of this method will block until it
        can pop something from the queue, else it will try to get a value and yield None if queue is empty. If block
        is True and a timeout is given, block until timeout expires and then yield None if no item was received. See
        https://docs.python.org/3/library/queue.html#queue.Queue.get for more information
        """
        while not self._msg_queue.empty():
            yield self.pop_msg(block=block, timeout=timeout)

    def has_messages(self) -> bool:
        """
        Returns a boolean flag indicating whether the queue has messages in it or not
        """
        return not self._msg_queue.empty()

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
        Returns a boolean indicating whether the auto client is set up and running
        """
        return self._is_running

    def start(self) -> bool:
        """
        Initiates connection to the server and starts the receiving loop on a new thread. Raises TimeoutError,
        ConnectionError, and socket.gaierror. Returns False if server object itself terminates the connection and
        True if the connection was successfully opened.
        """
        if self._is_running:
            return False
        result = self._tcp_client.connect()
        if not result:
            return result
        self._is_running = True
        th = threading.Thread(target=self._receive_loop)
        th.start()
        logger.info(f"Auto client started.")
        return result

    def stop(self):
        """
        Stops the auto client. If the client is not running, this method will do nothing.
        """
        if self._is_running:
            self._is_running = False
            self._tcp_client.disconnect()
            logger.info(f"Auto client stopped.")
