"""
TCPClient.py
Written by: Joshua Kitchen - 2024
"""

import logging
import socket

import TCPLib.internals.tcp_obj as tcp_obj


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
