"""
listener.py
Written by: Joshua Kitchen - 2024
"""
import logging
import random
import socket

from ..logger.logger import config_logger, LogLevels, toggle_stream_handler


class Listener:
    '''Listens for and accepts new client connections for the server'''
    def __init__(self, host, port, server_obj, log_path, log_level=LogLevels.INFO, timeout=None):
        self._addr = (host, port)
        self._soc = None
        self._server_obj = server_obj
        self._timeout = timeout
        self.log_path = log_path
        self.log_level = log_level
        self.logger = logging.getLogger(__name__)
        config_logger(self.logger, log_path, log_level)

    @staticmethod
    def _generate_client_id():
        client_id = str(random.randint(0, 999999))
        client_id = int(client_id, base=36)
        return str(client_id)

    def toggle_console_logging(self):
        toggle_stream_handler(self.logger, self.log_level)

    def timeout(self):
        return self._timeout

    def set_timeout(self, timeout):
        self._timeout = timeout
        if self._soc:
            self._soc.settimeout(timeout)

    def addr(self):
        return self._addr

    def create_soc(self):
        self._soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._soc.settimeout(self._timeout)
        try:
            self._soc.bind(self._addr)
        except socket.gaierror:
            self.logger.exception(f"Exception when trying to bind to {self._addr[0]} @ {self._addr[1]}")
            return False
        return True

    def close(self):
        self._soc.close()
        self._soc = None
        self.logger.debug("Listener socket has been closed")

    def mainloop(self):
        self.logger.debug("Listener.mainloop has started")
        while self._server_obj.is_running():
            self.logger.debug("Listening for new connections")
            try:
                self._soc.listen()
                client_soc, client_addr = self._soc.accept()
                self.logger.info(f"Accepted Connection from {client_addr[0]} @ {client_addr[1]}")
                if self._server_obj.is_full():
                    self.logger.debug(f"{client_addr[0]} @ {client_addr[1]} was denied connection due to server being full")
                    client_soc.close()
                    continue
                self._server_obj.start_client_proc(self._generate_client_id(),
                                                   client_addr[0],
                                                   client_addr[1],
                                                   client_soc)

            except OSError:
                self.logger.exception(f"Exception occurred while listening on {self._addr[0]} @ {self._addr[1]}")
                break
        self.logger.debug("Listener.mainloop has stopped")
