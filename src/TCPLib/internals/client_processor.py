"""
client_processor.py
Written by: Joshua Kitchen - 2024
"""

import logging
import threading
import queue

from ..active_client import ActiveTcpClient


logging.getLogger(__name__)


class ClientProcessor(ActiveTcpClient):
    '''Maintains a single client connection for the server'''
    def __init__(self, client_id, host, port, server_obj, msg_queue: queue.Queue, client_soc, buff_size=4096):
        ActiveTcpClient.__init__(self, host, port, msg_queue, buff_size, client_id)
        self._server_obj = server_obj
        self._client_soc = client_soc

    def id(self):
        return self._client_id

    def start(self):
        self._tcp_client.connect(self._host, self._port, self._client_soc)
        self._is_running = True
        th = threading.Thread(target=self._receive_loop)
        th.start()
