"""
auto_tcp_client.py
Written by: Joshua Kitchen - 2024
"""

import logging
import queue
import threading

from .msg_flags import Flags
from .tcp_client import TCPClient
from .internals.message import Message

logger = logging.getLogger(__name__)


class AutoTCPClient:
    '''A basic TCP client that automatically listens for messages from a server'''
    def __init__(self, host: str = None, port: int = None, client_id: str = None, msg_queue: queue.Queue = None,
                 buff_size: int = 4096, timeout: int = None):
        self._tcp_client = TCPClient(host=host, port=port, timeout=timeout)
        self._is_running = False
        self._client_id = client_id
        self._buff_size = buff_size

        if msg_queue:
            self._msg_queue = msg_queue
        else:
            self._msg_queue = queue.Queue()

    def _clean_up(self):
        self._tcp_client.disconnect(warn=False)
        self._is_running = False

    def _receive_loop(self):
        logger.debug("Client %s is listening for new messages from %s @ %d",
                     self._client_id, self.addr()[0], self.addr()[1])
        while self._is_running:
            size, flags, data = self._tcp_client.receive_all(self._buff_size)
            if data is None:
                continue
            if flags == 4:
                self._clean_up()
                self._msg_queue.put(Message(self._client_id, size, flags, data))
                return
            self._msg_queue.put(Message(self._client_id, size, flags, data))



    def pop_msg(self, block: bool = False, timeout: int = None):
        try:
            return self._msg_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def get_all_msg(self, block: bool = False, timeout: int = None):
        while not self._msg_queue.empty():
            yield self.pop_msg(block=block, timeout=timeout)

    def has_messages(self):
        return not self._msg_queue.empty()

    def clear_messages(self):
        with self._msg_queue.mutex:
            self._msg_queue.queue.clear()

    def id(self):
        return self._client_id

    def timeout(self):
        return self._tcp_client.timeout()

    def set_timeout(self, timeout: int):
        self._tcp_client.set_timeout(timeout)

    def send(self, data: bytes, flags: int = Flags.DATA):
        return self._tcp_client.send(data, flags)

    def addr(self):
        return self._tcp_client.addr()

    def set_addr(self, host: str, port: int):
        return self._tcp_client.set_addr(host, port)

    def is_running(self):
        return self._is_running

    def start(self):
        if self._is_running:
            return False
        result = self._tcp_client.connect()
        if not result or isinstance(result, Exception):
            return result
        self._is_running = True
        th = threading.Thread(target=self._receive_loop)
        th.start()
        logger.info(f"Auto client started.")
        return result

    def stop(self, warn: bool = False):
        self._is_running = False
        self._tcp_client.disconnect(warn=warn)
        logger.info(f"Auto client stopped.")
