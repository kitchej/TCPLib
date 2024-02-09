import logging
import threading

import tcp_obj
from message import Message

logging.getLogger(__name__)


class ClientProcessor(tcp_obj.TCPObj):
    def __init__(self, host, port, server_obj, client_soc, client_id, buff_size=4096):
        tcp_obj.TCPObj.__init__(self, host, port, buff_size)
        self._server_obj = server_obj
        self._soc = client_soc
        self._client_id = client_id
        self._client_completed_recv = False
        self._client_completed_recv_lock = threading.Lock()

    def disconnect(self, warn=True):
        if self._is_connected:
            if warn:
                self.send_bytes(b'', tcp_obj.DISCONNECT)
            self._soc.close()
            logging.info(f"{self._client_id}: Client at {self._addr[0]} @ {self._addr[1]} was disconnected")
            self._soc = None
            self._addr = ()
            self._is_connected = False
            self._server_obj.disconnect_client(client_id=self._client_id)

    def client_completed_recv(self):
        self._client_completed_recv_lock.acquire()
        if self._client_completed_recv != (False, ()):
            result = self._client_completed_recv
            self._client_completed_recv = (False, ())
        else:
            result = None
        self._client_completed_recv_lock.release()
        return result

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
                self._server_obj.messages.append(Message(self._client_id, size, flags, data))
                self.send_bytes(len(data).to_bytes(4, byteorder='little'), tcp_obj.COUNT)
            elif flags == 4:
                self.disconnect(warn=False)
