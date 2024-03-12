"""
client_processor.py
Written by: Joshua Kitchen - 2024
"""

import logging
import threading
import queue

from ..logger.logger import config_logger, LogLevels, toggle_stream_handler
from ..active_client import ActiveTcpClient


class ClientProcessor(ActiveTcpClient):
    '''Maintains a single client connection for the server'''
    def __init__(self, client_id, host, port, msg_queue: queue.Queue, client_soc,
                 log_path, log_level=LogLevels.INFO, buff_size=4096):
        ActiveTcpClient.__init__(self, host, port, msg_queue, client_id, log_path, log_level, buff_size)
        self._client_soc = client_soc
        self.log_path = log_path
        self.log_level = log_level
        self.logger = logging.getLogger(__name__)
        config_logger(self.logger, log_path, log_level)

    def start(self):
        self._tcp_client.connect(self._host, self._port, self._client_soc)
        self._is_running = True
        th = threading.Thread(target=self._receive_loop)
        th.start()
        self.logger.info(f"Processing {self._tcp_client.addr()[0]} @ {self._tcp_client.addr()[1]} "
                         f"as client #{self._client_id}")
