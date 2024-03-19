"""
active_client.py
Written by: Joshua Kitchen - 2024
"""

import logging
import queue
import threading

from .passive_client import PassiveTcpClient
from .internals.message import Message

logger = logging.getLogger(__name__)

# Message flags
COUNT = 1
DATA = 2
DISCONNECT = 4


class ActiveTcpClient:
    '''Once started, connects to the host and always listens for messages'''
    def __init__(self, host, port, client_id, msg_queue: queue.Queue = None, buff_size=4096):
        self._tcp_client = PassiveTcpClient(host=host, port=port)
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
        while self._is_running:
            logger.debug("Client %s is listening for new messages from %s @ %d",
                         self._client_id, self.addr()[0], self.addr()[1])
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

    def pop_msg(self, block=False):
        try:
            return self._msg_queue.get(block=block)
        except queue.Empty:
            return None

    def get_all_msg(self, block=False):
        while not self._msg_queue.empty():
            yield self.pop_msg(block=block)

    def has_messages(self):
        return not self._msg_queue.empty()

    def id(self):
        return self._client_id

    def timeout(self):
        return self._tcp_client.timeout()

    def set_timeout(self, timeout: int):
        self._tcp_client.set_timeout(timeout)

    def send(self, data: bytes, flags: int = DATA):
        return self._tcp_client.send(data, flags)

    def addr(self):
        return self._tcp_client.addr()

    def is_running(self):
        return self._is_running

    def start(self):
        self._tcp_client.connect()
        self._is_running = True
        th = threading.Thread(target=self._receive_loop)
        th.start()
        logger.info(f"Active client started. Connected to %s @ %d",
                    self.addr()[0], self.addr()[1])

    def stop(self, warn=False):
        self._is_running = False
        self._tcp_client.disconnect(warn=warn)
        logger.info(f"Active client stopped. Disconnected from %s @ %d", self.addr()[0], self.addr()[1])
