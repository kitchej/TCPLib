import logging
import threading

import tcp_obj as tcp_obj
from message import Message

logging.getLogger(__name__)


class ClientProcessor(tcp_obj.TCPObj):
    '''Maintains a single client connection for the server'''
    def __init__(self, host, port, server_obj, client_soc, client_id, buff_size=4096):
        tcp_obj.TCPObj.__init__(self, host, port)
        self._server_obj = server_obj
        self._soc = client_soc
        self._client_id = client_id
        self._client_completed_recv = (False, ())
        self._client_completed_recv_lock = threading.Lock()
        self._is_connected = True

    def id(self):
        return self._client_id

    def disconnect(self, warn=True):
        if self._is_connected:
            if warn:
                self.send(b'', tcp_obj.DISCONNECT)
            self._soc.close()
            logging.info(f"{self._client_id}: Client at {self._addr[0]} @ {self._addr[1]} was disconnected")
            self._soc = None
            self._is_connected = False

    def client_completed_recv(self):
        self._client_completed_recv_lock.acquire()
        if self._client_completed_recv != (False, ()):
            result = self._client_completed_recv
            self._client_completed_recv = (False, ())
        else:
            result = None
        self._client_completed_recv_lock.release()
        return result

    def send(self, data: bytes, flags: int):
        msg = self.encode_msg(data, flags)
        result = self.send_bytes(msg)
        if result:
            while self._is_connected:
                self._client_completed_recv_lock.acquire()
                if self._client_completed_recv[0]:
                    result = self._client_completed_recv[1]
                    self._client_completed_recv = (False, None)
                    self._client_completed_recv_lock.release()
                    break
                self._client_completed_recv_lock.release()
        return result

    def receive(self, buff_size):
        bytes_recv = 0
        size, flags = self.decode_header(self.receive_bytes(5))
        if not size:
            yield from None

        while bytes_recv < size:
            data = self._soc.recv(buff_size)
            if not data:
                yield from None
            bytes_recv += len(data)
            remaining = size - bytes_recv
            if remaining < buff_size:
                buff_size = remaining
            yield data
        yield from None

    def process_client(self):
        logging.debug(f"{self._client_id}: Waiting for messages from {self._addr[0]} @ {self._addr[1]}")
        while self._server_obj.is_running():
            msg = self.receive_bytes()
            if msg == ():
                self.disconnect(warn=False)
                logging.debug(
                    f"{self._client_id}: No longer waiting for messages from {self._addr[0]} @ {self._addr[1]}")
                return

            size, flags, data = msg[0], msg[1], msg[2]

            logging.debug(f"Received message from {self._client_id}:\n"
                          f"\tSIZE = {size}\n"
                          f"\tFLAGS = {flags}\n"
                          f"\tDATA = \n\n"
                          f"{data}\n\n")

            if flags == 1:
                self._client_completed_recv_lock.acquire()
                self._client_completed_recv = (True, (size, flags, data))
                self._client_completed_recv_lock.release()
            elif flags == 2:
                self._server_obj._messages.put(Message(self._client_id, size, flags, data))
                self.send_bytes(len(data).to_bytes(4, byteorder='big'), tcp_obj.COUNT)
            elif flags == 4:
                self.disconnect(warn=False)
