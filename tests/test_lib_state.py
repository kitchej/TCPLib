import threading
import time
import logging
import os
import pytest

from tests.globals_for_tests import setup_log_folder, HOST, PORT
from src.log_util import add_file_handler
from src.TCPLib.tcp_client import NoAddressSupplied

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_folder = setup_log_folder("TestLibState")


class TestLibState:
    def test_server_state(self, dummy_client, server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_server_state.log"),
                         logging.DEBUG,
                         "test_server_state-filehandler")

        assert server.addr == (HOST, PORT)
        assert not server.is_running
        assert not server.is_full
        assert server.max_clients == 0
        assert server.timeout is None

        server.addr = ("123.456.789", 9000)
        assert server.addr == ("123.456.789", 9000)
        server.addr = (HOST, PORT)
        assert server.addr == (HOST, PORT)

        server.start()
        time.sleep(0.1)

        assert server.is_running
        assert not server.is_full
        assert server.max_clients == 0
        assert server.timeout is None

        server.timeout = 10
        assert server.timeout == 10
        try:
            server.timeout = -1
        except Exception as e:
            if isinstance(e, ValueError):
                assert True
            else:
                assert False
        try:
            server.timeout = -25
        except Exception as e:
            if isinstance(e, ValueError):
                assert True
            else:
                assert False
        assert server.timeout == 10
        server.timeout = None

        server.max_clients = 1
        assert server.max_clients == 1
        try:
            server.max_clients = -1
        except Exception as e:
            if isinstance(e, ValueError):
                assert True
            else:
                assert False
        try:
            server.max_clients = -25
        except Exception as e:
            if isinstance(e, ValueError):
                assert True
            else:
                assert False
        server.max_clients = 1

        dummy_client.connect((HOST, PORT))
        time.sleep(0.2)
        assert server.client_count == 1
        assert server.is_full is True

        assert server.list_clients()
        conn_client = server.list_clients()[0]

        client_proc = server._get_client(conn_client)
        client_info = server.get_client_info(conn_client)

        try:
            assert client_info["is_running"] is True
            assert client_info["timeout"] is None
            assert client_info["addr"] == (HOST, client_proc._tcp_client._addr[1])
        except KeyError:
            assert False

        server.set_clients_timeout(10)
        assert server.get_client_info(conn_client)["timeout"] == 10
        assert server.set_clients_timeout(-1) is False
        assert server.get_client_info(conn_client)["timeout"] == 10

        server.disconnect_client(conn_client)

        assert server.is_full is False
        assert server.client_count == 0

        server.stop()

        assert server.addr == (HOST, PORT)
        assert not server.is_running
        assert not server.is_full
        assert server.max_clients == 1

    def test_client_state(self, dummy_server, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_client_state.log"),
                         logging.DEBUG,
                         "test_client_state-filehandler")
        assert client.timeout is None
        assert client.is_connected is False

        client.timeout = 10
        assert client.timeout == 10

        client.addr = ("123.456.789", 9000)
        assert client.addr == ("123.456.789", 9000)
        client.addr = (None, None)
        try:
            client.connect()
        except NoAddressSupplied:
            assert True
        client.addr = (HOST, PORT)
        assert client.addr == (HOST, PORT)
        client.connect()
        time.sleep(0.1)
        assert client.is_connected is True
        client.addr = ("123.456.789", 9000)
        assert client.addr == (HOST, PORT)

        client.disconnect()

        assert client.addr == (HOST, PORT)
        assert client.is_connected is False

    @pytest.mark.parametrize('client_list', [2], indirect=True)
    def test_client_to_client_state(self, client_list):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_client_to_client_state.log"),
                         logging.DEBUG,
                         "test_client_to_client_state-filehandler")

        client1 = client_list[0]
        client2 = client_list[1]

        client1.addr = (None, None)
        try:
            client1.host_single_client()
        except NoAddressSupplied:
            assert True
        client1.addr = (HOST, PORT)


        threading.Thread(target=client1.host_single_client).start()
        time.sleep(0.1)
        client2.connect()
        time.sleep(0.1)

        assert client1.is_connected is True
        assert client2.is_connected is True
        assert client1.addr == (HOST, PORT)
        assert client2.addr == (HOST, PORT)
        assert client1.host_single_client() is False
        assert client2.host_single_client() is False



