import src.TCPLib.tcp_server as tcp_server
import os
import logging
import threading
import socket
import traceback

from server_interface import ServerInterface


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


HOST = "127.0.0.1"
PORT = 5000

with open(os.path.join("tests", "dummy_files", "one-gig-vid.mkv"), 'rb') as file:
    video = file.read()

with open(os.path.join("tests", "dummy_files", "DOI.txt"), 'rb') as file:
    text = file.read()


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
        PORT,
        r"tests/logs\Server.log",
        logging.DEBUG
    )
    s.start()

    while True:
        print(f"Waiting for clients: {s.client_count()} clients connected")
        while s.client_count() != 1:
            continue

        print(f"Sending {len(message)} bytes to Client")
        client_id = s.list_clients()[0]
        result = s.send(client_id, message)
        if not result:
            s.disconnect_client(s.list_clients()[0], warn=False)
            continue

        reply = s.pop_msg(block=True)

        print(f"REPLY = Size: {reply.size} | Flags: {reply.flags} | Data: {int.from_bytes(reply.data, byteorder='big')}\n")
        s.disconnect_client(client_id, warn=False)


def use_dummy(message):
    s = DummyServer(HOST, PORT)

    while True:
        print("Waiting for client")
        client_soc, client_addr = s.listen()
        print(f"Connected to {client_addr}")
        print(f"Sending {len(message)} bytes to Client")
        result = s.send(message, client_soc)
        print(f"REPLY = {result}\n")


def use_interface():
    s = tcp_server.TCPServer(
        "192.168.0.2",
        PORT,
        r"tests/logs\Server.log",
        logging.DEBUG
    )
    s.start()
    inter = ServerInterface(s)

    # s.toggle_console_log()

    th = threading.Thread(target=inter.mainloop)
    th.start()
    th.join()


# use_dummy(text)
# use_dummy(video)

# use_real(text)
# use_real(video)

use_interface()
