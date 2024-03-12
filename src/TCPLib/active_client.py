"""
active_client.py
Written by: Joshua Kitchen - 2024
"""

import logging
import queue
import threading

from .logger.logger import config_logger, LogLevels, toggle_stream_handler
from .passive_client import PassiveTcpClient
from .internals.message import Message

# Message flags
COUNT = 1
DATA = 2
DISCONNECT = 4


class ActiveTcpClient:
    '''Once started, always listens for messages'''
    def __init__(self, host, port, msg_queue: queue.Queue, client_id, log_path, log_level=LogLevels.INFO, buff_size=4096):
        self._tcp_client = PassiveTcpClient(host, port, log_path, log_level)
        self._is_running = False
        self._host = host
        self._port = port
        self._client_id = client_id
        self._buff_size = buff_size
        self._msg_queue = msg_queue
        self.log_path = log_path
        self.log_level = log_level
        self.logger = logging.getLogger(__name__)
        config_logger(self.logger, log_path, log_level)

    def _clean_up(self):
        self._tcp_client.disconnect(warn=False)
        self._is_running = False

    def _receive_loop(self):
        while self._is_running:
            self.logger.debug(f"Client {self._client_id} is listening for new messages from "
                              f"{self._tcp_client.addr()[0]} @ {self._tcp_client.addr()[1]}")
            msg = self._tcp_client.receive_all(self._buff_size)
            if not msg:
                self._clean_up()
                return
            size, flags, data = msg[0], msg[1], msg[2]
            self._msg_queue.put(Message(self._client_id, size, flags, data))
            if flags == 4:
                self._clean_up()
            if flags == 2:
                self._tcp_client.send(int.to_bytes(len(data), byteorder='big', length=4), 1)

    def toggle_console_logging(self):
        toggle_stream_handler(self.logger, self.log_level)

    def id(self):
        return self._client_id

    def timeout(self):
        return self._tcp_client.timeout()

    def set_timeout(self, timeout: int):
        self._tcp_client.set_timeout(timeout)

    def send(self, data: bytes, flags: int = DATA):
        return self._tcp_client.send(data, flags)

    def addr(self):
        return self._host, self._port

    def is_running(self):
        return self._is_running

    def start(self):
        self._tcp_client.connect(self._host, self._port)
        self._is_running = True
        th = threading.Thread(target=self._receive_loop)
        th.start()
        self.logger.info(f"Active client started. Connected to {self._tcp_client.addr()[0]} @ {self._tcp_client.addr()[1]}")

    def stop(self, warn=False):
        self._is_running = False
        self._tcp_client.disconnect(warn=warn)
        self.logger.info(f"Active client stopped. Disconnected from "
                    f"{self._tcp_client.addr()[0]} @ {self._tcp_client.addr()[1]}")
