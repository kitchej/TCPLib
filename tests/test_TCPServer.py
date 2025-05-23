import queue
import time
import logging
import os
import socket

import pytest

from globals_for_tests import setup_log_folder, HOST, PORT
from log_util import add_file_handler
from TCPLib.tcp_server import TCPServer

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_folder = setup_log_folder("TestTCPServer")


class TestTCPServer:
    @staticmethod
    def assert_default_state(server):
        assert server._addr == (None, None)
        assert server._max_clients == 0
        assert server._timeout is None
        assert isinstance(server._messages, queue.Queue)
        assert server._soc is None
        assert server._is_running is False
        assert len(server._connected_clients) == 0

    @pytest.mark.parametrize('client_list', [11], indirect=True)
    def test_class_state(self, server, client_list):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_class_state.log"),
                         logging.DEBUG,
                         "test_class_state-filehandler")
        self.assert_default_state(server)
        server.start((HOST, PORT))

        while not server.is_running:
            pass

        time.sleep(0.1)

        assert server._addr == (HOST, PORT)
        assert server._max_clients == 0
        assert server._timeout is None
        assert isinstance(server._messages, queue.Queue)
        assert server._soc is not None
        assert server._is_running is True
        assert len(server._connected_clients) == 0

        assert server.addr == (HOST, PORT)
        assert server.is_running is True
        server.max_clients = 10
        assert server.max_clients == 10
        server.timeout = 10
        assert server.timeout == 10
        server.timeout = None

        for i in range(10):
            time.sleep(0.1)
            client_list[i].connect((HOST, PORT))

        time.sleep(0.1)
        assert server.is_full is True
        assert server.client_count == 10

        client_list[10].connect((HOST, PORT))
        time.sleep(0.1)

        assert server.is_full is True
        assert server.client_count == 10

        server.set_clients_timeout(1)
        time.sleep(0.1)

        client_ids = server.list_clients()
        assert len(client_ids) == 10

        for client_id, client in zip(client_ids, client_list[:11]):
            info = server.get_client_info(client_id)
            assert info["is_running"] is True
            assert info["timeout"] == 1
            assert info["addr"] == client._soc.getsockname()

        server.disconnect_client(client_ids[0])
        assert server.is_full is False
        assert server.client_count == 9
        server.max_clients = 0
        assert server.max_clients == 0

        server.stop()
        time.sleep(0.1)
        self.assert_default_state(server)

    def test_from_socket(self, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_from_socket.log"),
                         logging.DEBUG,
                         "test_from_socket-filehandler")
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.bind((HOST, PORT))

        s = TCPServer.from_socket(soc)
        time.sleep(0.1)

        assert s._addr == (HOST, PORT)
        assert s._max_clients == 0
        assert s._timeout is None
        assert isinstance(s._messages, queue.Queue)
        assert s._soc is not None
        assert s._is_running is True
        assert len(s._connected_clients) == 0

        s.stop()

    """Test exception handling in _mainloop()"""

    @pytest.mark.parametrize('error_server', [(ConnectionError, "accept")], indirect=True)
    def test_mainloop_connection_error(self, error_server, dummy_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_mainloop_connection_error.log"),
                         logging.DEBUG,
                         "test_mainloop_connection_error-filehandler")

        time.sleep(0.1)
        dummy_client.connect((HOST, PORT))
        time.sleep(0.1)

        assert error_server._is_running
        assert error_server.client_count == 0

    @pytest.mark.parametrize('error_server', [(TimeoutError, "accept")], indirect=True)
    def test_mainloop_timeout_error(self, error_server, dummy_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_mainloop_timeout_error.log"),
                         logging.DEBUG,
                         "test_mainloop_timeout_error-filehandler")

        time.sleep(0.1)
        dummy_client.connect((HOST, PORT))
        time.sleep(0.1)

        assert error_server._is_running
        assert error_server.client_count == 0

    @pytest.mark.parametrize('error_server', [(AttributeError, "listen")], indirect=True)
    def test_mainloop_attribute_error(self, error_server, dummy_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_mainloop_attribute_error.log"),
                         logging.DEBUG,
                         "test_mainloop_attribute_error-filehandler")

        time.sleep(0.1)
        assert not error_server.is_running
        assert error_server.client_count == 0

    @pytest.mark.parametrize('error_server', [(OSError, "listen")], indirect=True)
    def test_mainloop_os_error(self, error_server, dummy_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_mainloop_os_error.log"),
                         logging.DEBUG,
                         "test_mainloop_os_error-filehandler")

        time.sleep(0.1)
        assert not error_server.is_running
        assert error_server.client_count == 0

    """Test message queue"""

    @pytest.mark.parametrize('client_list', [10], indirect=True)
    def test_pop_msg(self, server, client_list):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_pop_msg.log"),
                         logging.DEBUG,
                         "test_pop_msg-filehandler")

        server.start((HOST, PORT))
        time.sleep(0.1)

        for client in client_list:
            client.connect((HOST, PORT))

        time.sleep(0.1)

        for i, client in enumerate(client_list):
            client.send(bytes(f"Sent from client #{i}", encoding="utf-8"))

        time.sleep(0.1)
        assert server.has_messages()
        assert server._messages.qsize() == 10
        msg = server.pop_msg()
        assert server._messages.qsize() == 9
        assert msg

        for m in server.get_all_msg():
            assert m

        assert not server.has_messages()

    def test_send(self, server, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send.log"),
                         logging.DEBUG,
                         "test_send-filehandler")

        server.start((HOST, PORT))
        time.sleep(0.1)

        client.connect((HOST, PORT))
        time.sleep(0.1)

        client_id = server.list_clients()[0]

        assert not server.send("000000000", b"Hello World!")
        assert server.send(client_id, b"Hello World!")

        msg = client.receive()
        assert msg == b"Hello World!"









