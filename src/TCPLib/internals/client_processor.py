"""
client_processor.py
Written by: Joshua Kitchen - 2024
"""

import logging
import threading
import queue

from ..active_client import ActiveTcpClient

logger = logging.getLogger(__name__)


class ClientProcessor(ActiveTcpClient):
    '''Maintains a single client connection for the server'''
    def __init__(self, client_id, host, port, msg_queue: queue.Queue, client_soc, buff_size=4096):
        ActiveTcpClient.__init__(self,
                                 host=host,
                                 port=port,
                                 msg_queue=msg_queue,
                                 client_id=client_id,
                                 buff_size=buff_size)
        self._client_soc = client_soc

    def start(self):
        self._tcp_client.connect(self._client_soc)
        self._is_running = True
        th = threading.Thread(target=self._receive_loop)
        th.start()
        logger.info(f"Processing %s @ %d as client #%s", self.addr()[0], self.addr()[1], self._client_id)
