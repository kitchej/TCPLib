import queue
import threading
import pathlib
import os
import pytest
import time
import socket

from TCPLib.passive_client import PassiveTcpClient
from TCPLib.tcp_server import TCPServer, DEBUG
from TCPLib.active_client import ActiveTcpClient

HOST = "127.0.0.1"
PORT = 5000


class DummyServer:
    def __init__(self, host, port):
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.bind((host, port))

    def listen(self):
        try:
            self.soc.listen()
            _, _ = self.soc.accept()
        except ConnectionError:
            return
        except OSError:
            return

    def close(self):
        self.soc.close()
        self.soc = None


@pytest.fixture
def dummy_server():
    s = DummyServer(HOST, PORT)
    threading.Thread(target=lambda: s.listen()).start()
    time.sleep(0.1)
    yield s
    s.close()


@pytest.fixture
def server():
    s = TCPServer(
        HOST,
        PORT,
        logging_level=DEBUG,
        log_path=os.path.join(pathlib.Path.home(), ".server_log")
    )
    s.start()
    time.sleep(0.1)
    yield s
    s.stop()


@pytest.fixture
def dummy_client():
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    yield c
    c.close()


@pytest.fixture
def client():
    c = PassiveTcpClient(
        HOST,
        PORT)
    yield c
    c.disconnect()


@pytest.fixture
def a_client():
    msg_queue = queue.Queue()
    c = ActiveTcpClient(
        HOST,
        PORT,
        msg_queue)
    c.start()
    yield c, msg_queue
    c.stop()


@pytest.fixture
def client_list():
    clients = [PassiveTcpClient(HOST, PORT) for _ in range(10)]
    yield clients
    for client in clients:
        client.disconnect()
