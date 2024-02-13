import logging
import threading
import queue

from TCPLib.internals.listener import Listener
from TCPLib.internals.client_processor import ClientProcessor

# Bindings for log levels, so the user doesn't have to import the logging module for one parameter

INFO = logging.INFO
DEBUG = logging.DEBUG


class TCPServer:
    def __init__(self, host, port, max_clients=0, buff_size=4096, timeout=None, logging_level=INFO, log_path=".server_log.txt"):
        self._max_clients = max_clients
        self._buff_size = buff_size
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

    def default_buff_size(self):
        return self._buff_size

    def set_default_buff_size(self, new_size):
        self._buff_size = new_size
        if self.client_count() != 0:
            for client_id in self.list_clients():
                self.edit_client_prop(client_id, buff_size=new_size)

    def set_listener_timeout(self, timeout):
        self._listener.set_timeout(timeout)

    def listener_timeout(self):
        return self._listener.timeout()

    def list_clients(self):
        self._connected_clients_lock.acquire()
        client_list = self._connected_clients.keys()
        self._connected_clients_lock.release()
        return list(client_list)

    def edit_client_prop(self, client_id, timeout=None, buff_size=None):
        client = self._get_client(client_id)
        if not client:
            return False
        if timeout:
            client.set_timeout(timeout)
        if buff_size:
            client.set_buff_size(buff_size)
        return True

    def get_client_info(self, client_id):
        client = self._get_client(client_id)
        if not client:
            return
        return {
            "is_connected": client.is_connected(),
            "addr": client.addr(),
            "timeout": client.timeout(),
            "buff_size": client.buff_size(),
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
        if client.is_connected():
            client.disconnect(warn=warn)
        return True

    def pop_msg(self, block=False):
        try:
            return self._messages.get(block=block)
        except queue.Empty:
            return None

    def get_all_msg(self):
        while not self._messages.empty():
            yield self.pop_msg()

    def send(self, client_id: str, data: bytes):
        self._connected_clients_lock.acquire()
        try:
            client = self._connected_clients[client_id]
        except KeyError:
            self._connected_clients_lock.release()
            return False
        self._connected_clients_lock.release()
        reply = client.send(data)
        if not reply:
            return reply
        else:
            return reply[0], reply[1], int.from_bytes(reply[2], byteorder="little")


    def start(self):
        if self._is_running:
            return False
        if not self._listener.create_soc():
            return False
        self._is_running = True
        threading.Thread(target=self._listener.mainloop).start()
        return True

    def close(self):
        if self._is_running:
            self._is_running = False
            self._listener.close()
            self._connected_clients_lock.acquire()
            for client in self._connected_clients.values():
                client.disconnect()
            self._connected_clients.clear()
            self._connected_clients_lock.release()
            logging.info("SERVER: Server has been shutdown")
