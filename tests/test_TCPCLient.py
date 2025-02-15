import threading
import threading
import time
import logging
import os
import socket

import pytest

from tests.globals_for_tests import setup_log_folder, HOST, PORT
from src.log_util import add_file_handler
from src.TCPLib.tcp_client import TCPClient

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_folder = setup_log_folder("TestTCPClient")


class TestTCPClient:
    def test_init(self, client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_init.log"),
                         logging.DEBUG,
                         "test_init-filehandler")
        dummy_server.start()

        assert client._soc is None
        assert client._listen_soc is None
        assert client._remote_addr == (None, None)
        assert client._host_addr == (None, None)
        assert client._timeout is None
        assert client._is_connected is False

        client.connect((HOST, PORT))

        assert isinstance(client._soc, socket.socket)
        assert client._listen_soc is None
        assert client._remote_addr == (None, None)
        assert client._host_addr == (HOST, PORT)
        assert client._timeout is None
        assert client._is_connected is True

        assert client.is_connected
        client.is_connected = False
        assert client.is_connected

        assert client.timeout is None
        client.timeout = 10
        assert client.timeout == 10
        assert client._soc.timeout == 10

        assert client.host_addr == (HOST, PORT)
        client.host_addr = ("192.168.010", 6000)
        assert client.host_addr == (HOST, PORT)

        client.disconnect()

        assert client._soc is None
        assert client._listen_soc is None
        assert client._remote_addr == (None, None)
        assert client._host_addr == (None, None)
        assert client._timeout is 10
        assert client._is_connected is False

    def test_connect_exp(self, dummy_server, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_connect_exp.log"),
                         logging.DEBUG,
                         "test_connect_exp-filehandler")

        client.timeout = 0.1
        try:
            client.connect((HOST, PORT))
        except Exception as e:
            assert isinstance(e, TimeoutError)

        client.timeout = None
        try:
            client.connect((HOST, PORT))
        except Exception as e:
            assert isinstance(e, ConnectionError)

        try:
            client.connect(("1234", 5000))
        except Exception as e:
            assert isinstance(e, socket.gaierror)

        # Test catch osError (If I can figure out a good way to raise it)

    def test_host_single_client(self, client, dummy_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_host_single_client.log"),
                         logging.DEBUG,
                         "test_host_single_client-filehandler")
        assert client._soc is None
        assert client._listen_soc is None
        assert client._remote_addr == (None, None)
        assert client._host_addr == (None, None)
        assert client._timeout is None
        assert client._is_connected is False

        try:
            client.host_single_client((HOST, PORT), timeout=0.1)
        except Exception as e:
            assert isinstance(e, TimeoutError)

        threading.Thread(target=client.host_single_client, args=[(HOST, PORT), 5]).start()
        time.sleep(0.1)
        dummy_client.connect((HOST, PORT))
        time.sleep(0.1)

        assert isinstance(client._soc, socket.socket)
        assert client._listen_soc is None
        assert client._remote_addr == dummy_client.getsockname()
        assert client._host_addr == (None, None)
        assert client._timeout is None
        assert client._is_connected is True

        client.disconnect()

        assert client._soc is None
        assert client._listen_soc is None
        assert client._remote_addr == (None, None)
        assert client._host_addr == (None, None)
        assert client._timeout is None
        assert client._is_connected is False

