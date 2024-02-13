import logging
import socket

import TCPLib.internals.tcp_obj as tcp_obj


# Bindings for log levels, so the user doesn't have to import the logging module for one parameter

INFO = logging.INFO
DEBUG = logging.DEBUG


class TCPClient(tcp_obj.TCPObj):
    def __init__(self, host, port, buff_size=4096, logging_level=INFO, log_path=".server_log.txt"):
        tcp_obj.TCPObj.__init__(self, host, port, buff_size)
        logging.basicConfig(filename=log_path, filemode='w', level=logging_level,
                            format="%(asctime)s - %(levelname)s: %(message)s",
                            datefmt="%m/%d/%Y %I:%M:%S %p")

    def send(self, data: bytes):
        if self.send_bytes(data, tcp_obj.DATA):
            reply = self.receive_bytes()
            return reply[0], reply[1], int.from_bytes(reply[2], byteorder="little")

    def receive(self):
        size, flags, data = self.receive_bytes()
        reply = len(data).to_bytes(4, byteorder="little")
        self.send_bytes(reply, tcp_obj.COUNT)

        return size, flags, data

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
                self.send_bytes(b'', tcp_obj.DISCONNECT)
            self._soc.close()
            logging.info(f"Disconnected from host {self._addr[0]} @ {self._addr[1]}")
            self._soc = None
            self._is_connected = False
            return True

        return False
