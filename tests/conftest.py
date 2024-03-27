"""
conftest.py
Written by: Joshua Kitchen - 2024
"""

import threading
import pytest
import time
import socket
import os
import shutil

from TCPLib.passive_client import PassiveTcpClient
from TCPLib.tcp_server import TCPServer
from TCPLib.active_client import ActiveTcpClient

# from src.TCPLib.passive_client import PassiveTcpClient
# from src.TCPLib.tcp_server import TCPServer
# from src.TCPLib.active_client import ActiveTcpClient

from tests.globals_for_tests import HOST, PORT


def pytest_collection_modifyitems(items):
    """
    Provided by user 'swimmer' on stackoverflow.com, modified slightly
    https://stackoverflow.com/questions/70738211/run-pytest-classes-in-custom-order/70758938#70758938

    Modifies test items in place to ensure test classes run in a given order.
    """
    CLASS_ORDER = ["TestLibState"]
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
def client():
    c = PassiveTcpClient(
        host=HOST,
        port=PORT
    )
    yield c
    c.disconnect()


@pytest.fixture
def active_client():
    c = ActiveTcpClient(
        host=HOST,
        port=PORT,
        client_id="Active_Client_Standalone"
    )
    yield c
    c.stop()


@pytest.fixture
def client_list(request):
    num_clients = request.param
    clients = [PassiveTcpClient(host=HOST, port=PORT) for _ in range(num_clients)]
    yield clients
    for client in clients:
        client.disconnect()


@pytest.fixture
def active_client_list(request):
    num_clients = request.param
    clients = [ActiveTcpClient(host=HOST, port=PORT, client_id=f"Client-{i}") for i in range(num_clients)]
    yield clients
    for client in clients:
        client.stop()
