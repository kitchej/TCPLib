import logging
import socket

import internals.tcp_obj as tcp_obj


# Bindings for log levels, so the user doesn't have to import the logging module for one parameter

INFO = logging.INFO
DEBUG = logging.DEBUG


class TCPClient(tcp_obj.TCPObj):
    '''Class for connecting and transmitting data to a remote server.'''
    def __init__(self, host, port, logging_level=INFO, log_path=".server_log.txt"):
        tcp_obj.TCPObj.__init__(self, host, port)
        logging.basicConfig(filename=log_path, filemode='w', level=logging_level,
                            format="%(asctime)s - %(levelname)s: %(message)s",
                            datefmt="%m/%d/%Y %I:%M:%S %p")

    def send(self, data: bytes, flags: int):
        msg = self.encode_msg(data, flags)
        if self.send_bytes(msg):
            reply = self.receive_bytes(9)
            return reply[0], reply[1], int.from_bytes(reply[2], byteorder='big')

    def receive(self, buff_size):
        bytes_recv = 0
        size, flags = self.decode_header(self.receive_bytes(5))
        if not size:
            yield from None

        while bytes_recv < size:
            data = self._soc.recv(buff_size)
            if not data:
                yield from None
            bytes_recv += len(data)
            remaining = size - bytes_recv
            if remaining < buff_size:
                buff_size = remaining
            yield data
        yield from None

    # def receive(self):
    #     size, flags, data = self.receive_bytes()
    #     reply = len(data).to_bytes(4, byteorder='big')
    #     self.send_bytes(reply, tcp_obj.COUNT)
    #
    #     return size, flags, data

    def connect(self, host: str, port: int):
        self._addr = (host, port)
        self._soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._soc.settimeout(self._timeout)
        logging.info(f"Connecting to {self._addr[0]} @ {self._addr[1]}")

        try:
            self._soc.connect(self._addr)
        except TimeoutError as e:
            self.disconnect(warn=False)
            logging.debug("Connection timed out")
            return e
        except ConnectionError as e:
            self.disconnect(warn=False)
            logging.debug("Connection was lost")
            return e
        except socket.gaierror as e:
            self.disconnect(warn=False)
            logging.exception("Could not connect")
            return e
        self._is_connected = True
        logging.info(f"Connected to {self._addr[0]} @ {self._addr[1]}")

    def disconnect(self, warn=True):
        if self._is_connected:
            if warn:
                self.send(b'', tcp_obj.DISCONNECT)
            self._soc.close()
            logging.info(f"Disconnected from host {self._addr[0]} @ {self._addr[1]}")
            self._soc = None
            self._is_connected = False
            return True

        return False
