"""
listener.py
Written by: Joshua Kitchen - 2024
"""
import logging
import random
import socket

from .utils import encode_msg

logger = logging.getLogger(__name__)


class Listener:
    '''Listens for and accepts new client connections for the server'''
    def __init__(self, host, port, server_obj, timeout=None):
        self._addr = (host, port)
        self._soc = None
        self._server_obj = server_obj
        self._timeout = timeout

    @staticmethod
    def _generate_client_id():
        client_id = str(random.randint(0, 999999))
        client_id = int(client_id, base=36)
        return str(client_id)

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
            logger.exception(f"Exception when trying to bind to %s @ %d", self._addr[0], self._addr[1])
            return False
        return True

    def close(self):
        self._soc.close()
        self._soc = None
        logger.debug("Listener socket has been closed")

    def mainloop(self):
        while self._server_obj.is_running():
            logger.debug("Listening for new connections")
            try:
                self._soc.listen()
                client_soc, client_addr = self._soc.accept()
                logger.info("Accepted Connection from %s @ %d", client_addr[0], client_addr[1])
                if self._server_obj.is_full():
                    logger.debug("%s @ %d was denied connection due to server being full",
                                 client_addr[0], client_addr[1])
                    client_soc.sendall(encode_msg(b'0', 4))
                    client_soc.close()
                    continue
                client_soc.sendall(encode_msg(b'0', 2))
                self._server_obj.start_client_proc(self._generate_client_id(),
                                                   client_addr[0],
                                                   client_addr[1],
                                                   client_soc)
            except OSError:
                logger.exception(f"Exception occurred while listening on %s @ %d", self._addr[0], self._addr[1])
                break
