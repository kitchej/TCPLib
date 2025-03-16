"""
conftest.py
Written by: Joshua Kitchen - 2024
"""
import queue
import pytest
import time
import socket
import os
import shutil

import dummy_soc
from TCPLib.tcp_client import TCPClient
from TCPLib.tcp_server import TCPServer
from TCPLib.client_processor import ClientProcessor


from globals_for_tests import HOST, PORT, DUMMY_ID


def pytest_collection_modifyitems(items):
    """
    Provided by user 'swimmer' on stackoverflow.com, modified slightly
    https://stackoverflow.com/questions/70738211/run-pytest-classes-in-custom-order/70758938#70758938

    Modifies test items in place to ensure test classes run in a given order.
    """
    CLASS_ORDER = ["TestClientProcessor", "TestTCPClient", "TestUtils"]
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

@pytest.fixture
def error_client(request):
    soc = dummy_soc.SocRaiseErr(excep=request.param[0], func_to_fail=request.param[1])
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    c = TCPClient.from_socket(soc)
    yield c
    if c._soc is not None:
        c._soc.close()


@pytest.fixture
def dummy_server():
    time.sleep(0.1)
    s = dummy_soc.DummyServer(HOST, PORT)
    yield s
    s.stop()


@pytest.fixture
def dummy_client():
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    yield c
    c.close()


@pytest.fixture
def server():
    s = TCPServer()
    yield s
    s.stop()

@pytest.fixture
def client_processor(dummy_client, dummy_server):
    dummy_server.start()
    dummy_client.connect((HOST, PORT))
    time.sleep(0.1)
    p = ClientProcessor(DUMMY_ID, dummy_server.soc, queue.Queue())
    yield p, dummy_client
    p.stop()
    dummy_client.close()
    dummy_server.stop()


@pytest.fixture
def error_client_processor(request, dummy_server):
    soc = dummy_soc.SocRaiseErr(excep=request.param[0], func_to_fail=request.param[1])
    dummy_server.start()
    soc.connect((HOST, PORT))
    time.sleep(0.1)
    p = ClientProcessor(DUMMY_ID, dummy_server.soc, queue.Queue())
    yield p, soc
    p.stop()
    soc.close()
    dummy_server.stop()


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
