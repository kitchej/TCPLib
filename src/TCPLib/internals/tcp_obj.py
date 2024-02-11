import abc
import logging

logging.getLogger(__name__)

# Message flags
COUNT = 1
DATA = 2
DISCONNECT = 4


class TCPObj(abc.ABC):
    '''Abstract base class defining a send/receive interface'''
    def __init__(self, host, port, buff_size=4096):
        self._addr = (host, port)
        self._timeout = None
        self._buff_size = buff_size
        self._is_connected = False
        self._soc = None

    @staticmethod
    def encode_msg(data: bytes, flags: int):
        msg = bytearray()
        size = len(data).to_bytes(4, byteorder='little')
        flags = flags.to_bytes(1, byteorder='little')
        msg.extend(size)
        msg.extend(flags)
        msg.extend(data)
        return msg

    @staticmethod
    def decode_header(header: bytes):
        size = int.from_bytes(header[0:4], byteorder="little")
        flags = int.from_bytes(header[4:5], byteorder="little")
        return size, flags

    def is_connected(self):
        return self._is_connected

    def buff_size(self):
        return self._buff_size

    def set_buff_size(self, size: int):
        self._buff_size = size

    def timeout(self):
        return self._timeout

    def set_timeout(self, timeout: int):
        self._timeout = timeout
        if self._soc:
            self._soc.settimeout(self._timeout)

    def addr(self):
        return self._addr

    @abc.abstractmethod
    def disconnect(self, warn=True):
        '''
        If warn is set to true, a disconnect message will be sent to the server.
        WARNING: If disconnecting after an error, warn should ALWAYS equal False
        otherwise bad things will happen.
        '''
        pass

    def send_bytes(self, data: bytes, flags: int):
        msg = self.encode_msg(data, flags)
        try:
            self._soc.sendall(msg)
            logging.debug(f"Sent msg to {self._addr[0]} @ {self._addr[1]}")
            return True
        except ConnectionAbortedError:
            logging.exception(f"Exception occurred while receiving from {self._addr[0]} @ {self._addr[1]}")
            self._is_connected = False
            return ()
        except ConnectionError:
            logging.exception(f"Exception occurred while receiving from {self._addr[0]} @ {self._addr[1]}")
            self.disconnect(warn=False)
            return False
        except OSError:
            logging.exception(f"Exception occurred while receiving from {self._addr[0]} @ {self._addr[1]}")
            self.disconnect(warn=False)
            return False
        except AttributeError:  # Socket was closed from another thread
            return False

    def receive_bytes(self):
        buff_size = self._buff_size
        data = bytearray()
        try:
            header = self._soc.recv(5)
            size, flags = self.decode_header(header)
            if size < buff_size:
                buff_size = size
            while len(data) < size:
                chunk = self._soc.recv(buff_size)
                data.extend(chunk)
                chunk_len = len(chunk)
                if chunk_len < buff_size:
                    buff_size = chunk_len
        except ConnectionAbortedError:
            logging.exception(f"Exception occurred while receiving from {self._addr[0]} @ {self._addr[1]}")
            self._is_connected = False
            return ()
        except ConnectionError:
            logging.exception(f"Exception occurred while receiving from {self._addr[0]} @ {self._addr[1]}")
            self._is_connected = False
            return ()
        except OSError:
            self._is_connected = False
            logging.exception(f"Exception occurred while receiving from {self._addr[0]} @ {self._addr[1]}")
            return ()
        except AttributeError:  # Socket was closed from another thread
            return ()

        return size, flags, data
