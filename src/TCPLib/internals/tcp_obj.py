"""
tcp_obj.py
Written by: Joshua Kitchen - 2024
"""

import abc
import logging
import queue
import threading

logging.getLogger(__name__)

# Message flags
COUNT = 1
DATA = 2
DISCONNECT = 4


class TCPObj(abc.ABC):
    '''Abstract base class defining a TCP send/receive interface'''
    def __init__(self, host, port):
        self._addr = (host, port)
        self._timeout = None
        self._is_connected = False
        self._soc = None
        self._recv_ended = False
        self._recv_ended_lock = threading.Lock()
        self._chunks = queue.Queue()

    def _clean_up(self):
        logging.exception(f"Exception occurred while receiving from {self._addr[0]} @ {self._addr[1]}")
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

    def disconnect(self, warn=True):
        """
        If warn is set to true, a disconnect message will be sent to the server.
        WARNING: If disconnecting after an error, warn should ALWAYS be False
        otherwise bad things will happen.
        """
        if self._is_connected:
            if warn:
                self.send_bytes(self.encode_msg(b'', DISCONNECT))
            if self._soc is not None:
                self._soc.close()
                self._soc = None
            logging.info(f"Disconnected from host {self._addr[0]} @ {self._addr[1]}")
            self._is_connected = False
            return True
        return False

    def send_bytes(self, data: bytes):
        """
        Send all bytes. No header creation or waiting for a report of bytes received.
        """
        try:
            self._soc.sendall(data)
            logging.debug(f"Sent msg to {self._addr[0]} @ {self._addr[1]}")
            return True
        except ConnectionAbortedError:
            self._clean_up()
            return False
        except ConnectionError:
            self._clean_up()
            return False
        except OSError:
            self._clean_up()
            return False
        except AttributeError:  # Socket was closed from another thread
            self._clean_up()
            return False

    def send(self, data: bytes, flags: int = DATA):
        """
        Send all bytes with a header and wait for a response from the receiver
        """
        msg = self.encode_msg(data, flags)
        if self.send_bytes(msg):
            reply = self.receive_bytes(9)
            size, flags = self.decode_header(reply[0:6])
            return size, flags, int.from_bytes(reply[6:], byteorder='big')

    def receive_bytes(self, size: int):
        """
        Receive only the number of bytes specified. No header processing and no received bytes are reported.
        """
        try:
            return self._soc.recv(size)
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
        Returns a generator for iterating over the bytes in an incoming message. First returns the size and flags, then
        all bytes in the message. Sends a response back with the number of bytes received.
        """
        bytes_recv = 0
        header = self.receive_bytes(5)
        if not header:
            return
        size, flags = self.decode_header(header)
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
        msg = self.encode_msg(bytes_recv.to_bytes(4, byteorder="big"), COUNT)
        self.send_bytes(msg)

    def receive_all(self, buff_size):
        """
        Receive all the bytes of an incoming message in one, easy method. Sends a response back with the number of
        bytes received.
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
        return size, flags, data
