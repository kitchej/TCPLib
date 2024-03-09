"""
tcp_server.py
Written by: Joshua Kitchen - 2024
"""

import logging
import threading
import queue

from .internals.listener import Listener
from .internals.client_processor import ClientProcessor
from .internals.message import Message

# Bindings for log levels, so the user doesn't have to import the logging module for one parameter

INFO = logging.INFO
DEBUG = logging.DEBUG

# Message flags
COUNT = 1
DATA = 2
DISCONNECT = 4


class TCPServer:
    '''Class for creating, maintaining, and transmitting data to multiple client connections.'''
    def __init__(self, host, port, max_clients=0, timeout=None, logging_level=INFO, log_path=".server_log.txt"):
        self._max_clients = max_clients
        self._connected_clients = {}
        self._connected_clients_lock = threading.Lock()
        self._messages = queue.Queue()
        self._is_running = False
        self._listener = Listener(host=host,
                                  port=port,
                                  server_obj=self,
                                  timeout=timeout)

        logging.basicConfig(filename=log_path, filemode='w', level=logging_level,
                            format="%(asctime)s - %(levelname)s: %(message)s",
                            datefmt="%m/%d/%Y %I:%M:%S %p")

    def _get_client(self, client_id):
        self._connected_clients_lock.acquire()
        try:
            client = self._connected_clients[client_id]
        except KeyError:
            self._connected_clients_lock.release()
            return
        self._connected_clients_lock.release()

        return client

    def start_client_proc(self, client_id, host, port, client_soc):
        client_proc = ClientProcessor(client_id=client_id,
                                      host=host,
                                      port=port,
                                      client_soc=client_soc,
                                      msg_queue=self._messages)

        client_proc.start()
        self.update_connected_clients(client_proc.id(), client_proc)
        logging.info(f"SERVER: Client at {client_proc.addr()[0]} @ {client_proc.addr()[1]} was connected")

    def update_connected_clients(self, client_id: str, client: ClientProcessor):
        self._connected_clients_lock.acquire()
        self._connected_clients.update({client_id: client})
        self._connected_clients_lock.release()

    def addr(self):
        return self._listener.addr()

    def is_running(self):
        return self._is_running

    def client_count(self):
        self._connected_clients_lock.acquire()
        count = len(self._connected_clients.keys())
        self._connected_clients_lock.release()

        return count

    def is_full(self):
        if self._max_clients > 0:
            if self.client_count() == self._max_clients:
                return True

        return False

    def max_clients(self):
        return self._max_clients

    def set_max_clients(self, new_max: int):
        self._max_clients = new_max

    def set_listener_timeout(self, timeout):
        self._listener.set_timeout(timeout)

    def listener_timeout(self):
        return self._listener.timeout()

    def list_clients(self):
        self._connected_clients_lock.acquire()
        client_list = self._connected_clients.keys()
        self._connected_clients_lock.release()
        return list(client_list)

    def get_client_info(self, client_id):
        client = self._get_client(client_id)
        if not client:
            return
        return {
            "is_running": client.is_running(),
            "addr": client.addr()
        }

    def disconnect_client(self, client_id: str, warn=True):
        self._connected_clients_lock.acquire()
        try:
            client = self._connected_clients[client_id]
        except KeyError:
            self._connected_clients_lock.release()
            return False
        del self._connected_clients[client_id]
        self._connected_clients_lock.release()
        if client.is_running():
            client.stop(warn=warn)
        return True

    def put_msg(self, msg: Message, block=False):
        self._messages.put(msg, block=block)

    def pop_msg(self, block=False):
        try:
            return self._messages.get(block=block)
        except queue.Empty:
            return None

    def get_all_msg(self, block=False):
        while not self._messages.empty():
            yield self.pop_msg(block=block)

    def has_messages(self):
        return self._messages.empty()

    def send(self, client_id: str, data: bytes):
        self._connected_clients_lock.acquire()
        try:
            client = self._connected_clients[client_id]
        except KeyError:
            self._connected_clients_lock.release()
            return False
        self._connected_clients_lock.release()
        return client.send(data, 2)

    def start(self):
        if self._is_running:
            return False
        if not self._listener.create_soc():
            return False
        self._is_running = True
        threading.Thread(target=self._listener.mainloop).start()
        return True

    def stop(self):
        if self._is_running:
            self._is_running = False
            self._listener.close()
            self._connected_clients_lock.acquire()
            for client in self._connected_clients.values():
                client.stop()
            self._connected_clients.clear()
            self._connected_clients_lock.release()
            logging.info("SERVER: Server has been shutdown")
