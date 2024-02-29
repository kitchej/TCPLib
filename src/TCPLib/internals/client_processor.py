"""
client_processor.py
Written by: Joshua Kitchen - 2024
"""

import logging
import threading

import TCPLib.internals.tcp_obj as tcp_obj
import TCPLib.internals.message as message

logging.getLogger(__name__)


class ClientProcessor(tcp_obj.TCPObj):
    '''Maintains a single client connection for the server'''
    def __init__(self, host, port, server_obj, client_soc, client_id, buff_size=4096):
        tcp_obj.TCPObj.__init__(self, host, port)
        self._server_obj = server_obj
        self._soc = client_soc
        self._client_id = client_id
        self._is_connected = True
        self._client_completed_recv = ()
        self._client_completed_recv_con = threading.Condition()

    def id(self):
        return self._client_id

    def send(self, data: bytes, flags: int = tcp_obj.DATA):
        return self.send_bytes(self.encode_msg(data, flags))

    def process_client(self, buff_size=4096):
        logging.debug(f"{self._client_id}: Waiting for messages from {self._addr[0]} @ {self._addr[1]}")
        while self._server_obj.is_running():
            msg = self.receive_all(buff_size)
            if not msg:
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
                self._server_obj._messages.put(message.Message(self._client_id, size, flags, data))
            elif flags == 2:
                self._server_obj._messages.put(message.Message(self._client_id, size, flags, data))
                self.send(len(data).to_bytes(4, byteorder='big'), tcp_obj.COUNT)
            elif flags == 4:
                self.disconnect(warn=False)
