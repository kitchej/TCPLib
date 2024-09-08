"""
tcp_client.py
Written by: Joshua Kitchen - 2024
"""
import logging
import socket
from typing import Generator

from .message import Message
from .internals.utils import encode_msg, decode_header

logger = logging.getLogger(__name__)


class NoAddressSupplied(Exception):
    pass


class TCPClient:
    """
    A basic TCP client.
    """

    def __init__(self, host: str = None, port: int = None, timeout: int = None):
        self._soc = None
        self._addr = (host, port)
        self._timeout = timeout
        self._is_connected = False

    @classmethod
    def from_socket(cls, soc: socket.socket):
        """
        Allows for a client to be created from a socket object.
        The socket must be initialized and connected.
        """
        out = cls(None, None, soc.gettimeout())
        out._soc = soc
        out._addr = soc.getsockname()
        out._is_connected = True
        return out

    def _clean_up(self):
        self.disconnect()
        self._is_connected = False

    def is_connected(self) -> bool:
        """
        Returns a boolean flag indicating whether the client is connected
        """
        return self._is_connected

    def timeout(self) -> int | None:
        """
        Returns an int representing the current timeout value.
        """
        return self._timeout

    def set_timeout(self, timeout: int) -> bool:
        """
        Sets how long the client will wait for messages from the server (in seconds). The Timeout argument should be
        a positive integer. Setting to zero will cause network operations to fail if no data is received immediately.
        Passing 'None' will set the timeout to infinity. Returns True on success, False if not. See
        https://docs.python.org/3/library/socket.html#socket-timeouts for more information about timeouts.
        """
        if timeout is None:
            pass
        elif timeout < 0:
            return False
        self._timeout = timeout
        if self._soc:
            self._soc.settimeout(self._timeout)
            return True

    def set_addr(self, host: str, port: int):
        """
        Allows for the address to be changed after class creation. If the server is running, this function will do
        nothing.
        """
        if self._is_connected:
            return
        self._addr = (host, port)

    def addr(self) -> tuple[str, int]:
        """
        Returns a tuple with the host's ip (str) and the port (int)
        """
        return self._addr

    def connect(self) -> bool:
        """
        Initiates a connection to the server. Raises TimeoutError, ConnectionError, and socket.gaierror.
        Returns False if server object refused the connection and True if the connection was
        accepted.
        """
        if self._addr == (None, None):
            raise NoAddressSupplied()
        if self._is_connected:
            return False

        self._soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._soc.settimeout(self._timeout)
        logger.info("Attempting to connect to %s @ %d", self._addr[0], self._addr[1])

        try:
            self._soc.connect(self._addr)
            size = decode_header(self._soc.recv(4))
            msg = self._soc.recv(size)
        except TimeoutError as e:
            self._clean_up()
            logger.error("Timed out trying to connect to %s @ %d", self._addr[0], self._addr[1])
            raise e
        except ConnectionError as e:
            logger.error("Connection error while trying to connect to %s @ %d", self._addr[0], self._addr[1])
            self._clean_up()
            raise e
        except socket.gaierror as e:
            logger.exception("Exception while trying to connect to %s @ %d", self._addr[0], self._addr[1])
            self._clean_up()
            raise e

        if msg == b'CONNECTION ACCEPTED':
            self._is_connected = True
            logger.info("Successfully connected to %s @ %d", self._addr[0], self._addr[1])
            return True
        elif msg == b'SERVER FULL':
            self._clean_up()
            logger.error("Connection to %s @ %d was denied due to the server being full",
                         self._addr[0], self._addr[1])
            return False
        else:
            self._clean_up()
            logger.error("Unrecognized reply from %s @ %d. Size=%d", self._addr[0], self._addr[1], size)
            return False

    def disconnect(self):
        """
        Disconnect from the currently connected server. If no connection is openened, this method does nothing.
        """
        if self._is_connected:
            if self._soc is not None:
                self._soc.close()
                self._soc = None
            logger.info("Disconnected from %s @ %d", self._addr[0], self._addr[1])
            self._is_connected = False

    def send_bytes(self, data: bytes):
        """
        Send all bytes of the data argument WITHOUT a header attached. Returns True on successful transmission,
        False on failed transmission. Raises TimeoutError, ConnectionError, socket.gaierror, and OSError.
        """
        if not self._is_connected:
            return False
        try:
            self._soc.sendall(data)
            logger.debug("Sent %d bytes to %s @ %d", len(data), self._addr[0], self._addr[1])
            return True
        except ConnectionError as e:
            self._clean_up()
            logger.exception("Exception occurred while sending to %s @ %d", self._addr[0], self._addr[1])
            raise e
        except socket.gaierror as e:
            self._clean_up()
            logger.exception("Exception occurred while sending to %s @ %d", self._addr[0], self._addr[1])
            raise e
        except OSError as e:
            self._clean_up()
            logger.exception("Exception occurred while sending to %s @ %d", self._addr[0], self._addr[1])
            raise e
        except AttributeError:  # Socket was closed from another thread
            self._clean_up()
            return False

    def send(self, data: bytes) -> bool:
        """
        Send all bytes of the data argument WITH a header attached. Returns True on successful transmission,
        False on failed transmission. Raises TimeoutError, ConnectionError, socket.gaierror, and OSError.
        """
        result = self.send_bytes(encode_msg(data))
        return result

    def receive_bytes(self, size: int) -> bytes | None:
        """
        Receive only the number of bytes specified, None if connection was closed prematurely. Raises TimeoutError,
        ConnectionError, socket.gaierror, and OSError.
        """
        try:
            data = self._soc.recv(size)
            return data
        except ConnectionError as e:
            self._clean_up()
            logger.exception("Exception occurred while receiving from to %s @ %d", self._addr[0], self._addr[1])
            raise e
        except socket.gaierror as e:
            self._clean_up()
            logger.exception("Exception occurred while receiving from to %s @ %d", self._addr[0], self._addr[1])
            raise e
        except OSError as e:
            self._clean_up()
            logger.exception("Exception occurred while receiving from %s @ %d", self._addr[0], self._addr[1])
            raise e
        except AttributeError:  # Socket was closed from another thread
            self._clean_up()
            return

    def receive(self, buff_size: int = 4096) -> Generator[bytes | int, None, None]:
        """
        Returns a generator for iterating over the bytes of an incoming message. An int representing the message size is
        yielded first. Subsequent calls yield the contents of the message as it is received. Raises TimeoutError,
        ConnectionError, socket.gaierror, and OSError.
        """
        if not self._is_connected:
            return
        if buff_size <= 0:
            return
        bytes_recv = 0
        header = self.receive_bytes(4)
        if not header:
            return
        size = decode_header(header)
        logger.info("Incoming message from %s @ %d, SIZE=%d",
                    self._addr[0], self._addr[1], size)
        yield size
        if size < buff_size:
            buff_size = size
        while bytes_recv < size:
            data = self.receive_bytes(buff_size)
            if not data:
                return
            bytes_recv += len(data)
            remaining = size - bytes_recv
            if remaining < buff_size:
                buff_size = remaining
            yield data

    def receive_all(self, buff_size: int = 4096) -> Message:
        """
        Receive all the bytes of an incoming message in one, easy method. Raises TimeoutError, ConnectionError,
        socket.gaierror, and OSError.
        """
        msg = Message(None, None)
        if not self._is_connected:
            return msg
        data = bytearray()
        gen = self.receive(buff_size)
        if not gen:
            return msg
        try:
            msg.size = next(gen)
        except StopIteration:
            return msg
        for chunk in gen:
            if not chunk:
                return msg
            data.extend(chunk)
        msg.data = data
        logger.debug("Received a total of %d bytes from %s @ %d", len(data), self._addr[0], self._addr[1])
        return msg
