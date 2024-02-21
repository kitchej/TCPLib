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


class ChunkInfo:
    def __init__(self, chunk_size, total_size):
        self.chunk_size = chunk_size
        self.total_size = total_size


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
        '''
        MSG STRUCTURE:
        [Header: 5 bytes] [Data: inf bytes]

        HEADER STRUCTURE:
        [Size: 4 bytes] [Flags: 1 Byte ->
                                         1 ----
                                         1     |
                                         1     | --- CURRENTLY UNUSED
                                         1     |
                                         1 ____
                                         1: DISCONNECTING
                                         1: TRANSMITTING DATA
                                         1: REPORTING BYTES RECEIVED
                        ]

        '''
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

    def query_progress(self):
        self._recv_ended_lock.acquire()
        ended = self._recv_ended
        self._recv_ended_lock.release()
        if not ended:
            yield self._chunks.get(block=True)
        else:
            if self._chunks.empty():
                yield from None
            else:
                yield self._chunks.get()

    @abc.abstractmethod
    def disconnect(self, warn=True):
        '''
        If warn is set to true, a disconnect message will be sent to the server.
        WARNING: If disconnecting after an error, warn should ALWAYS equal False
        otherwise bad things will happen.
        '''
        pass

    def send_bytes(self, data: bytes):
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

    def receive_bytes(self, size: int):
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


    # def receive_bytes(self):
    #     buff_size = self._buff_size
    #     data = bytearray()
    #     self._recv_ended_lock.acquire()
    #     self._recv_ended = False
    #     self._recv_ended_lock.release()
    #     try:
    #         header = self._soc.recv(5)
    #         size, flags = self.decode_header(header)
    #
    #         if size < buff_size:
    #             buff_size = size
    #         while len(data) < size:
    #             chunk = self._soc.recv(buff_size)
    #             data.extend(chunk)
    #             chunk_len = len(chunk)
    #             if chunk_len < buff_size:
    #                 buff_size = chunk_len
    #
    #             self._chunks.put(ChunkInfo(chunk_len, size))
    #
    #     except ConnectionAbortedError:
    #         self._clean_up()
    #         return ()
    #     except ConnectionError:
    #         self._clean_up()
    #         return ()
    #     except OSError:
    #         self._clean_up()
    #         return ()
    #     except AttributeError:  # Socket was closed from another thread
    #         self._clean_up()
    #         return ()
    #
    #     self._recv_ended_lock.acquire()
    #     self._recv_ended = True
    #     self._recv_ended_lock.release()
    #
    #     return size, flags, data
