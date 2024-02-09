import logging

import internals.tcp_obj as tcp_obj


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
        pass

    def receive(self):
        pass

    def connect(self, addr: str, port: int):
        pass

    def disconnect(self, warn=True):
        pass
