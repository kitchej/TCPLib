"""
client_processor.py
Written by: Joshua Kitchen - 2024
"""

import logging
import threading
import queue

from ..auto_tcp_client import AutoTCPClient
from ..tcp_client import TCPClient

logger = logging.getLogger(__name__)


class ClientProcessor(AutoTCPClient):
    '''Maintains a single client connection for the server'''
    def __init__(self, client_id, host, port, msg_queue: queue.Queue, client_soc, server_obj,
                 buff_size=4096, timeout: int = None):
        AutoTCPClient.__init__(self,
                               host=host,
                               port=port,
                               msg_queue=msg_queue,
                               client_id=client_id,
                               buff_size=buff_size,
                               timeout=timeout)
        self._tcp_client = TCPClient.from_socket(client_soc)
        self._server_obj = server_obj
        self._is_running = True
        th = threading.Thread(target=self._receive_loop)
        th.start()
        logger.info(f"Processing %s @ %d as client #%s", self.addr()[0], self.addr()[1], self._client_id)

    def _clean_up(self):
        self._server_obj.disconnect_client(self._client_id, warn=False)
