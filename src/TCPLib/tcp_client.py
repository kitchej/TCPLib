"""
tcp_client.py
Written by: Joshua Kitchen - 2024
"""
import logging
import socket

from .msg_flags import Flags
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
        self.disconnect(warn=False)
        self._is_connected = False

    def is_connected(self):
        return self._is_connected

    def timeout(self):
        return self._timeout

    def set_timeout(self, timeout: int):
        """
        Sets how long the client will wait for messages from the server. The Timeout argument should be a positive
        integer. Setting to zero will cause network operations to fail if no data is received immediately.
        Passing 'None' will set the timeout to infinity.
        See https://docs.python.org/3/library/socket.html#socket-timeouts for more information about timeouts.
        """
        self._timeout = timeout
        if self._soc:
            self._soc.settimeout(self._timeout)
            return True
        else:
            return False

    def set_addr(self, host: str, port: int):
        if self._is_connected:
            return False
        self._addr = (host, port)
        return True

    def addr(self):
        return self._addr

    def connect(self):
        """
        Initiates connection to the server. Raises TimeoutError, ConnectionError, and socket.gaierror.
        Returns False if server object itself terminates the connection and True if the connection was
        successfully opened.
        """
        if self._addr == (None, None):
            return NoAddressSupplied()
        if self._is_connected:
            return True
        self._soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._soc.settimeout(self._timeout)

        logger.info("Attempting to connect to %s @ %d", self._addr[0], self._addr[1])

        try:
            self._soc.connect(self._addr)
            confirm_conn = self._soc.recv(6)
            _, flags = decode_header(confirm_conn[:5])
            if flags == 4:
                self._soc.close()
                return False
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
        self._is_connected = True
        logger.info("Successfully connected to %s @ %d", self._addr[0], self._addr[1])
        return True

    def disconnect(self, warn: bool = False):
        """
        If warn is set to true, a disconnect message will be sent to the server.
        NOTE: When disconnecting after an error, warn should ALWAYS be False
        """
        if self._is_connected:
            if warn:
                self.send(b'', Flags.DISCONNECT)
            if self._soc is not None:
                self._soc.close()
                self._soc = None
            logger.info("Disconnected from %s @ %d", self._addr[0], self._addr[1])
            self._is_connected = False
            return True
        return False

    def send_bytes(self, data: bytes):
        """
        Send all bytes of 'data' WITHOUT a header attached
        """
        if not self._is_connected:
            return False
        try:
            self._soc.sendall(data)
            logger.debug("Sent %d bytes to %s @ %d", len(data), self._addr[0], self._addr[1])
            return True
        except ConnectionAbortedError:
            self._clean_up()
            return False
        except ConnectionError:
            self._clean_up()
            return False
        except OSError:
            self._clean_up()
            logger.exception("Exception occurred while sending to %s @ %d", self._addr[0], self._addr[1])
            return False
        except AttributeError:  # Socket was closed from another thread
            self._clean_up()
            return False

    def send(self, data: bytes, flags: int = Flags.DATA):
        """
        Send all bytes of 'data' WITH a header attached
        """
        msg = encode_msg(data, flags)
        result = self.send_bytes(msg)
        return result

    def receive_bytes(self, size: int):
        """
        Receive only the number of bytes specified. Does not process the header if attached
        """
        if not self._is_connected:
            return False
        try:
            data = self._soc.recv(size)
            return data
        except ConnectionAbortedError:
            self._clean_up()
            return
        except ConnectionError:
            self._clean_up()
            return
        except OSError:
            self._clean_up()
            return
        except AttributeError:  # Socket was closed from another thread
            self._clean_up()
            return

    def receive(self, buff_size: int = 4096):
        """
        Returns a generator for iterating over the bytes of an incoming message. Header information is returned first as
        a tuple containing the size and flags. Subsequent calls return the contents of the message as it is received.
        """
        if not self._is_connected:
            return
        if buff_size <= 0:
            return
        bytes_recv = 0
        header = self.receive_bytes(5)
        if not header:
            return
        size, flags = decode_header(header)
        logger.info("Incoming message from %s @ %d:\n\tSIZE: %d\n\tFLAGS: %d",
                    self._addr[0], self._addr[1], size, flags)
        yield size, flags
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

    def receive_all(self, buff_size: int = 4096):
        """
        Receive all the bytes of an incoming message in one, easy method.
        """
        msg = Message(None, None, None, None)
        if not self._is_connected:
            return msg
        data = bytearray()
        gen = self.receive(buff_size)
        if not gen:
            return msg
        try:
            msg.size, msg.flags = next(gen)
        except StopIteration:
            return msg
        for chunk in gen:
            if not chunk:
                return msg
            data.extend(chunk)
        msg.data = data
        logger.debug("Received a total of %d bytes from %s @ %d", len(data), self._addr[0], self._addr[1])
        return msg
