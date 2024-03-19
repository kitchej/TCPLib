"""
passive_client.py
Written by: Joshua Kitchen - 2024
"""
import logging
import socket

logger = logging.getLogger(__name__)

# Message flags
COUNT = 1
DATA = 2
DISCONNECT = 4


class PassiveTcpClient:
    '''Only receives and sends data when told'''
    def __init__(self, host, port):
        self._addr = (host, port)
        self._timeout = None
        self._is_connected = False
        self._soc = None

    def _clean_up(self):
        self.disconnect(warn=False)
        self._is_connected = False

    @staticmethod
    def encode_msg(data: bytes, flags: int):
        """
        MSG STRUCTURE:
        [Header: 5 bytes] [Data: inf bytes]

        HEADER STRUCTURE:
        [Size: 4 bytes] [Flags: 1 Byte -> 1 ----
                                          1     |
                                          1     | --- CURRENTLY UNUSED
                                          1     |
                                          1 ____
                                          1: DISCONNECTING
                                          1: TRANSMITTING DATA
                                          1: REPORTING BYTES RECEIVED]
        """
        msg = bytearray()
        size = len(data).to_bytes(4, byteorder='big')
        flags = flags.to_bytes(1, byteorder='big')
        msg.extend(size)
        msg.extend(flags)
        msg.extend(data)
        return msg

    @staticmethod
    def decode_header(header: bytes):
        size = int.from_bytes(header[0:4], byteorder='big')
        flags = int.from_bytes(header[4:5], byteorder='big')
        return size, flags

    def is_connected(self):
        return self._is_connected

    def timeout(self):
        return self._timeout

    def set_timeout(self, timeout: int):
        self._timeout = timeout
        if self._soc:
            self._soc.settimeout(self._timeout)

    def addr(self):
        return self._addr

    def connect(self, soc: socket.socket = None):
        if soc:
            self._soc = soc
            self._soc.settimeout(self._timeout)
            return
        else:
            self._soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._soc.settimeout(self._timeout)

        logger.info("Connecting to %s @ %d", self._addr[0], self._addr[1])

        try:
            self._soc.connect(self._addr)
        except TimeoutError as e:
            self._clean_up()
            logger.error("Timed out trying to connect to %s @ %d", self._addr[0], self._addr[1])
            return e
        except ConnectionError as e:
            self._clean_up()
            return e
        except socket.gaierror as e:
            self._clean_up()
            return e
        self._is_connected = True
        logger.info("Connected to %s @ %d", self._addr[0], self._addr[1])

    def disconnect(self, warn=True):
        """
        If warn is set to true, a disconnect message will be sent to the server.
        NOTE: When disconnecting after an error, warn should ALWAYS be False
        """
        if self._is_connected:
            if warn:
                self.send_bytes(self.encode_msg(b'', DISCONNECT))
            if self._soc is not None:
                self._soc.close()
                self._soc = None
            logger.info("Disconnected from %s @ %d", self._addr[0], self._addr[1])
            self._is_connected = False
            return True
        return False

    def send_bytes(self, data: bytes):
        """
        Send all bytes unprocessed.
        """
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

    def send(self, data: bytes, flags: int = DATA):
        """
        Send all bytes with a header attached
        """
        msg = self.encode_msg(data, flags)
        result = self.send_bytes(msg)
        return result

    def receive_bytes(self, size: int):
        """
        Receive only the number of bytes specified.
        """
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

    def receive(self, buff_size):
        """
        Returns a generator for iterating over the bytes of an incoming message. The first item returned is the contents
        of the header, then all other calls return the bytes of a message.
        """
        bytes_recv = 0
        header = self.receive_bytes(5)
        if not header:
            return
        size, flags = self.decode_header(header)
        logger.info("Incoming message from %s @ %d:\n\tSIZE: %d\n\tFLAGS: %d",
                    self._addr[0], self._addr[1], size, flags)
        yield size, flags
        while bytes_recv < size:
            data = self.receive_bytes(buff_size)
            if not data:
                return
            bytes_recv += len(data)
            remaining = size - bytes_recv
            if remaining < buff_size:
                buff_size = remaining
            yield data

    def receive_all(self, buff_size):
        """
        Receive all the bytes of an incoming message in one, easy method.
        """
        data = bytearray()
        gen = self.receive(buff_size)
        try:
            size, flags = next(gen)
        except StopIteration:
            return
        for chunk in gen:
            if not chunk:
                return ()
            data.extend(chunk)
        logger.debug("Received a total of %d bytes from %s @ %d", len(data), self._addr[0], self._addr[1])
        return size, flags, data
