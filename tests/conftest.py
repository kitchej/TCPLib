"""
conftest.py
Written by: Joshua Kitchen - 2024
"""
import queue
import threading
import pytest
import time
import socket
import os
import shutil

from src.TCPLib.tcp_client import TCPClient
from src.TCPLib.tcp_server import TCPServer
from src.TCPLib.client_processor import ClientProcessor
from src.TCPLib.utils import encode_msg, decode_header

from tests.globals_for_tests import HOST, PORT, DUMMY_ID


def pytest_collection_modifyitems(items):
    """
    Provided by user 'swimmer' on stackoverflow.com, modified slightly
    https://stackoverflow.com/questions/70738211/run-pytest-classes-in-custom-order/70758938#70758938

    Modifies test items in place to ensure test classes run in a given order.
    """
    CLASS_ORDER = ["TestLibState", "TestUtils"]
    class_mapping = {item: item.cls.__name__ for item in items}
    sorted_items = items.copy()
    # Iteratively move tests of each class to the start of the test queue
    for class_ in CLASS_ORDER:
        sorted_items = [it for it in sorted_items if class_mapping[it] == class_] + \
                       [it for it in sorted_items if class_mapping[it] != class_]
    items[:] = sorted_items


def setup_log_folder(folder_name):
    log_folder = os.path.join("logs", folder_name)
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
    else:
        shutil.rmtree(log_folder)
        os.mkdir(log_folder)
    return log_folder


class ConfigurableClient:
    def __init__(self, host, port):
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host_addr = (HOST, PORT)

    def send(self, data: bytes, bandwith=0, latency=0):
        self.soc.sendall(data)

    def connect(self):
        self.soc.connect(self.host_addr)

    def close(self):
        if self.soc is not None:
            self.soc.close()
            self.soc = None


class DummyServer(ConfigurableClient):
    def __init__(self, host, port):
        ConfigurableClient.__init__(self, host, port)
        self.soc = None
        self.listen_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_soc.bind((host, port))

    def listen(self, delay):
        self.listen_soc.listen()
        time.sleep(delay)
        client_soc, _ = self.listen_soc.accept()
        self.soc = client_soc
        self.listen_soc.close()

    def start(self, delay=0):
        threading.Thread(target=self.listen, args=[delay]).start()
        time.sleep(0.1)


@pytest.fixture
def dummy_server():
    s = DummyServer(HOST, PORT)
    yield s
    s.close()

@pytest.fixture
def dummy_client():
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    yield c
    c.close()


@pytest.fixture
def server():
    s = TCPServer(
        host=HOST,
        port=PORT
    )
    time.sleep(0.1)
    yield s
    s.stop()

@pytest.fixture
def client_processor(dummy_client, dummy_server):
    dummy_server.start()
    dummy_client.connect((HOST, PORT))
    time.sleep(0.1)
    p = ClientProcessor(DUMMY_ID, dummy_server.soc, queue.Queue())
    yield p, dummy_client
    p._is_running = False


@pytest.fixture
def client():
    c = TCPClient()
    yield c
    c.disconnect()


@pytest.fixture
def client_list(request):
    num_clients = request.param
    clients = [TCPClient() for _ in range(num_clients)]
    yield clients
    for client in clients:
        client.disconnect()
