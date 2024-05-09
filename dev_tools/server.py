import os
import logging
import threading
import socket
import traceback

import src.TCPLib.tcp_server as tcp_server
from server_interface import ServerInterface
import dev_tools.log_util as log_util

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_util.add_file_handler(logger, "logs\\Server_Log", logging.DEBUG, "server-file-handler")
log_util.add_stream_handler(logger, logging.DEBUG, "server-stream-handler")


def encode_msg(data: bytes, flags: int):
    msg = bytearray()
    size = len(data).to_bytes(4, byteorder='big')
    flags = flags.to_bytes(1, byteorder='big')
    msg.extend(size)
    msg.extend(flags)
    msg.extend(data)
    return msg


def decode_header(header: bytes):
    size = int.from_bytes(header[0:4], byteorder='big')
    flags = int.from_bytes(header[4:5], byteorder='big')
    return size, flags


# HOST = "127.0.0.1"
HOST = "192.168.1.37"
PORT = 5000

# HOST = "192.168.1.32"
# PORT = 5000

# with open(os.path.join("dummy_files", "video1.mkv"), 'rb') as file:
#     video = file.read()
#
# with open(os.path.join("dummy_files", "DOI.txt"), 'rb') as file:
#     text = file.read()


class DummyServer:
    def __init__(self, host, port):
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.bind((host, port))
        self.lock = threading.Lock()
        self.client_connected = False

    def listen(self):
        try:
            self.soc.listen()
            result = self.soc.accept()
            return result
        except Exception as e:
            traceback.print_exception(e)

    def send(self, data, client):
        try:
            client.sendall(encode_msg(data, 2))
            reply = client.recv(9)[5:]
            return int.from_bytes(reply, byteorder='big')
        except Exception as e:
            traceback.print_exception(e)

    def receive(self):
        try:
            header = self.soc.recv(5)
            size, flags = decode_header(header)

            buff_size = 4096
            bytes_recv = 0
            while bytes_recv < size:
                data = self.soc.recv(buff_size)
                if not data:
                    yield
                bytes_recv += len(data)
                remaining = size - bytes_recv
                if remaining < buff_size:
                    buff_size = remaining
                yield data
            msg = encode_msg(bytes_recv.to_bytes(4, byteorder="big"), 1)
            self.soc.sendall(msg)
        except Exception as e:
            traceback.print_exception(e)

    def close(self):
        self.soc.close()
        self.soc = None


def use_real(message):
    s = tcp_server.TCPServer(
        HOST,
        PORT
    )
    s.start()

    while True:
        logging.info(f"Waiting for clients: {s.client_count()} clients connected")
        while s.client_count() != 1:
            continue

        client_id = s.list_clients()[0]
        result = s.send(client_id, message)
        if not result:
            s.disconnect_client(s.list_clients()[0], warn=False)
            continue

        reply = s.pop_msg(block=True)

        logging.info(f"REPLY = Size: {reply.size} | Flags: {reply.flags} | Data: {int.from_bytes(reply.data, byteorder='big')}\n")
        s.disconnect_client(client_id, warn=False)


def use_dummy(message):
    s = DummyServer(HOST, PORT)

    while True:
        logging.info("Waiting for client")
        client_soc, client_addr = s.listen()
        logging.info(f"Connected to {client_addr}")
        logging.info(f"Sending {len(message)} bytes to Client")
        result = s.send(message, client_soc)
        logging.info(f"REPLY = {result}\n")


def use_interface():
    s = tcp_server.TCPServer(HOST, PORT)
    inter = ServerInterface(s, logger=logger, auto_start=True)
    th = threading.Thread(target=inter.mainloop)
    th.start()
    th.join()


def save_files(save_dir):
    s = tcp_server.TCPServer(HOST, PORT)
    s.start()
    client_id = None

    while True:
        filename = s.pop_msg(block=True)
        if filename.data == b"DONE":
            client_id = filename.client_id
            break
        message = s.pop_msg(block=True)
        if message.data == b"DONE":
            break

        filename = str(filename.data, "utf-8")
        with open(os.path.join(save_dir, filename), 'wb') as file:
            file.write(message.data)

    s.send(client_id, b"DONE")


def send_file(filepath):
    s = tcp_server.TCPServer(HOST, PORT)
    s.start()
    filename = os.path.split(filepath)[-1]
    with open(filepath, 'rb') as file:
        data = file.read()

    while s.client_count() != 1:
        continue

    client_id = s.list_clients()[0]

    s.send(client_id, bytes(filename, 'utf-8'))
    s.send(client_id, data)





print(os.getcwd())

# use_dummy(text)
# use_dummy(video)

# use_real(text)
# use_real(video)

# use_interface()

# save_files(r"C:\Users\Josh\PycharmProjects\TCPLib\dev_tools\photo")

send_file(r"C:\Users\Josh\PycharmProjects\TCPLib\dist\TCP_Lib-1.0.0-py3-none-any.whl")

