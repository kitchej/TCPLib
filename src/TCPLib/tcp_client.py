"""
tcp_client.py
Written by: Joshua Kitchen - 2024
"""
import logging
import socket
from typing import Generator

from .utils import encode_msg, decode_header

logger = logging.getLogger(__name__)


class NegativeBufferValue(Exception):
    pass


class TCPClient:
    """
    A simple TCP client that can connect to a TCP/IP host
    """

    def __init__(self, timeout: int = None):
        self._soc = None
        self._listen_soc = None
        self._remote_addr = (None, None)
        self._host_addr = (None, None)
        self._timeout = timeout
        self._is_connected = False
        self._is_host = False

    @classmethod
    def from_socket(cls, soc: socket.socket) -> "TCPClient":
        """
        Allows for a client to be created from a socket object. The socket must be initialized and connected. Returns
        a new TCPClient object.
        """
        out = cls(soc.gettimeout())
        out._soc = soc
        try:
            out._host_addr = soc.getpeername()
        except OSError:  # Not connected
            return out
        out._is_connected = True
        return out

    def _clean_up(self):
        if self._soc is not None:
            self._soc.close()
            self._soc = None
        if self._listen_soc is not None:
            self._listen_soc.close()
            self._listen_soc = None
        self._remote_addr = (None, None)
        self._host_addr = (None, None)
        self._is_connected = False
        self._is_host = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @is_connected.setter
    def is_connected(self, value):
        return

    @property
    def timeout(self) -> int:
        return self._timeout

    @timeout.setter
    def timeout(self, timeout: int):
        if timeout is not None:
            if timeout < 0:
                raise ValueError("Value for timeout should be a positive integer")
        self._timeout = timeout
        if self._soc:
            self._soc.settimeout(self._timeout)

    @property
    def host_addr(self) -> tuple[str, int]:
        return self._host_addr

    @host_addr.setter
    def host_addr(self, value):
        return

    @property
    def remote_addr(self) -> tuple[str, int]:
        return self._remote_addr

    @remote_addr.setter
    def remote_addr(self, value):
        return

    @property
    def is_host(self) -> bool:
        return self._is_host

    @is_host.setter
    def is_host(self, value):
        return

    def host_single_client(self, addr: tuple[str, int], timeout: int = None):
        """
        Hosts a single connection from a remote TCP/IP connection. The timeout argument sets how long this
        method will listen for a connection. Raises TimeoutError, ConnectionError, and socket.gaierror.
        """
        if self._is_connected:
            return
        self._listen_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listen_soc.settimeout(timeout)
        self._listen_soc.bind(addr)
        try:
            self._listen_soc.listen()
            client_soc, client_addr = self._listen_soc.accept()
            self._soc = client_soc
            self._remote_addr = client_addr
            self._is_connected = True
            self._is_host = True
            logger.info("Accepted Connection from %s @ %d", client_addr[0], client_addr[1])
        except TimeoutError as e:
            self._clean_up()
            raise e
        except ConnectionError as e:
            self._clean_up()
            raise e
        except socket.gaierror as e:
            self._clean_up()
            raise e
        except OSError as e:
            self._clean_up()
            raise e
        self._listen_soc.close()
        self._listen_soc = None
        return

    def connect(self, addr: tuple[str, int]):
        """
        Initiates a connection to a TCP/IP host. Raises TimeoutError, ConnectionError, and socket.gaierror.
        """
        if self._is_connected:
            return
        if not self._soc:
            self._soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._soc.settimeout(self._timeout)
        self._host_addr = addr
        logger.info("Attempting to connect to %s @ %d", self._host_addr[0], self._host_addr[1])
        try:
            self._soc.connect(self._host_addr)
            self._is_connected = True
            self._is_host = False
        except TimeoutError as e:
            self._clean_up()
            raise e
        except ConnectionError as e:
            self._clean_up()
            raise e
        except socket.gaierror as e:
            self._clean_up()
            raise e
        except OSError as e:
            self._clean_up()
            raise e

    def disconnect(self):
        """
        Disconnect from the currently connected host. If no connection is opened, this method does nothing.
        """
        if self._is_connected:
            self._clean_up()
            logger.info("Disconnected from host")

    def send_bytes(self, data: bytes):
        """
        Send raw bytes with no size header. Raises TimeoutError, ConnectionError, and OSError.
        """
        if not self._is_connected:
            return False
        try:
            self._soc.sendall(data)
            return True
        except AttributeError:  # Socket was closed from another thread
            self._clean_up()
            return False
        except TimeoutError as e:
            self._clean_up()
            raise e
        except ConnectionError as e:
            self._clean_up()
            raise e
        except OSError as e:
            self._clean_up()
            raise e

    def send(self, data: bytes):
        """
        Send raw bytes with a 4 byte size header attached. Raises TimeoutError, ConnectionError, and OSError.
        """
        return self.send_bytes(encode_msg(data))

    def receive_bytes(self, size: int) -> bytes:
        """
        Receive only the number of bytes specified. Returns None if connection was closed prematurely. Raises TimeoutError,
        ConnectionError, and OSError.
        """
        try:
            data = self._soc.recv(size)
            return data
        except AttributeError:  # Socket was closed from another thread
            self._clean_up()
        except TimeoutError as e:
            self._clean_up()
            raise e
        except ConnectionError as e:
            self._clean_up()
            raise e
        except OSError as e:
            self._clean_up()
            raise e

    def iter_receive(self, buff_size: int = 4096) -> Generator:
        """
        Returns a generator for iterating over the bytes of an incoming message. An integer representing the message
        size is yielded first. Subsequent calls yield the contents of the message as it is received. Raises
        TimeoutError, ConnectionError, and OSError.
        """
        if not self._is_connected:
            return
        if buff_size <= 0:
            raise NegativeBufferValue("Argument buff_size must be a non-zero, positive integer")
        bytes_recv = 0
        header = self.receive_bytes(4)
        if not header:  # Socket was closed from another thread
            return
        size = decode_header(header)
        logger.debug("Incoming message from %s @ %d, SIZE=%d",
                     self._host_addr[0], self._host_addr[1], size)
        yield size
        if size < buff_size:
            buff_size = size
        while bytes_recv < size:
            data = self.receive_bytes(buff_size)
            if not data:  # Socket was closed from another thread
                return
            bytes_recv += len(data)
            remaining = size - bytes_recv
            if remaining < buff_size:
                buff_size = remaining
            yield data

    def receive(self, buff_size: int = 4096) -> bytearray:
        """
        Receive raw bytes. Expects a 4 bytes size header to be attached. Returns a bytearray. Raises TimeoutError, ConnectionError, and OSError.
        """
        data = bytearray()
        if not self._is_connected:
            return data
        gen = self.iter_receive(buff_size)
        if not gen:
            return data
        try:
            next(gen)
        except StopIteration:
            return data
        for chunk in gen:
            if not chunk:
                return data
            data.extend(chunk)
        if self._host_addr == (None, None):
            logger.debug("Received a total of %d bytes", len(data))
        else:
            logger.debug("Received a total of %d bytes from %s @ %d", len(data), self._host_addr[0], self._host_addr[1])
        return data
