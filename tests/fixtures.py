import threading
import pathlib
import os
import pytest
import time
import socket

import TCPLib.TCPClient as TCPClient
import TCPLib.TCPServer as TCPServer

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
    s = TCPServer.TCPServer(
        HOST,
        PORT,
        logging_level=TCPServer.DEBUG,
        log_path=os.path.join(pathlib.Path.home(), ".server_log")
    )
    s.start()
    time.sleep(0.1)
    yield s
    s.close()


@pytest.fixture
def dummy_client():
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    yield c
    c.close()


@pytest.fixture
def client():
    c = TCPClient.TCPClient(
        HOST,
        PORT,
        logging_level=TCPClient.DEBUG,
        log_path=os.path.join(pathlib.Path.home(), ".server_log")
    )
    yield c
    c.disconnect()


@pytest.fixture
def client_list():
    clients = [TCPClient.TCPClient(HOST, PORT, logging_level=TCPClient.DEBUG) for _ in range(10)]
    yield clients
    for client in clients:
        client.disconnect()
