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
        assert server._addr is None
        assert server._max_clients == 0
        assert server._timeout is None
        assert isinstance(server._messages, queue.Queue)
        assert server._soc is None
        assert server._is_running is False
        assert len(server._connected_clients) == 0


    @staticmethod
    def assert_msg_logged_mainloop(s, caplog, expected_txt, wait_time=2):
        found=False
        delay = time.time() + wait_time
        with caplog.at_level(logging.DEBUG):
            s.start((HOST, PORT))
            while not s.is_running:
                pass

            while time.time() < delay:
                if any(expected_txt in record.msg for record in caplog.records):
                    found = True
                    break
                time.sleep(0.05)
            if not found:
                raise AssertionError(f"Could not find \"{expected_txt}\" in logs")


    @pytest.mark.parametrize('client_list', [11], indirect=True)
    def test_class_state(self, server_no_start, client_list):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_class_state.log"),
                         logging.DEBUG,
                         "test_class_state-filehandler")

        self.assert_default_state(server_no_start)
        server_no_start.start((HOST, PORT))
        while not server_no_start.is_running:
            pass
        assert server_no_start._addr == (HOST, PORT)
        assert server_no_start._max_clients == 0
        assert server_no_start._timeout is None
        assert isinstance(server_no_start._messages, queue.Queue)
        assert server_no_start._soc is not None
        assert server_no_start._is_running is True
        assert len(server_no_start._connected_clients) == 0

        assert server_no_start.addr == (HOST, PORT)
        assert server_no_start.is_running is True
        server_no_start.max_clients = 10
        assert server_no_start.max_clients == 10
        server_no_start.timeout = 10
        assert server_no_start.timeout == 10
        server_no_start.timeout = None

        for i in range(10):
            time.sleep(0.1)
            client_list[i].connect((HOST, PORT))

        time.sleep(0.1)
        assert server_no_start.is_full is True
        assert server_no_start.client_count == 10

        client_list[10].connect((HOST, PORT))
        time.sleep(0.1)

        assert server_no_start.is_full is True
        assert server_no_start.client_count == 10

        client_ids = server_no_start.list_clients()
        assert len(client_ids) == 10

        server_no_start.disconnect_client(client_ids[0])
        assert server_no_start.is_full is False
        assert server_no_start.client_count == 9

        server_no_start.stop()
        time.sleep(0.1)
        server_no_start.max_clients = 0
        self.assert_default_state(server_no_start)

    @pytest.mark.parametrize('client_list', [10], indirect=True)
    def test_get_set_client_attributes(self, server, client_list):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_get_set_client_attributes.log"),
                         logging.DEBUG,
                         "test_get_set_client_attributes-filehandler")

        for client in client_list:
            client.connect((HOST, PORT))
            time.sleep(0.1)

        for client_id, client in zip(server.list_clients(), client_list[:11]):
            server.set_client_attribute(client_id, 'timeout', 30)
            server.set_client_attribute(client_id, 'max_timeouts', 29)
            with pytest.raises(ValueError):
                server.set_client_attribute(client_id, 'is_running', 30)
                server.set_client_attribute(client_id, 'addr', 30)
                server.set_client_attribute(client_id, 'total_timeouts', 30)


        for client_id, client in zip(server.list_clients(), client_list[:11]):
            info = server.get_client_attributes(client_id)
            assert info["is_running"] is True
            assert info["timeout"] == 30
            assert info["addr"][0] == HOST
            assert info["total_timeouts"] == 0
            assert info["max_timeouts"] == 29

    def test_from_socket(self, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_from_socket.log"),
                         logging.DEBUG,
                         "test_from_socket-filehandler")
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s = TCPServer.from_socket(soc, 10)
        s.start((HOST, PORT))
        time.sleep(0.1)

        assert s._addr == (HOST, PORT)
        assert s._max_clients == 10
        assert s._timeout is None
        assert isinstance(s._messages, queue.Queue)
        assert s._soc is not None
        assert s._is_running is True
        assert len(s._connected_clients) == 0

        s.stop()

    """Test exception handling in _mainloop()"""

    @pytest.mark.parametrize('error_server', [(ConnectionError, "accept")], indirect=True)
    def test_mainloop_connection_error(self, error_server, caplog):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_mainloop_connection_error.log"),
                         logging.DEBUG,
                         "test_mainloop_connection_error-filehandler")

        self.assert_msg_logged_mainloop(error_server, caplog, "New connection was disconnected before connection could be accepted")
        assert error_server._is_running

    @pytest.mark.parametrize('error_server', [(TimeoutError, "accept")], indirect=True)
    def test_mainloop_timeout_error(self, error_server, caplog):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_mainloop_timeout_error.log"),
                         logging.DEBUG,
                         "test_mainloop_timeout_error-filehandler")

        self.assert_msg_logged_mainloop(error_server, caplog, "New connection timed out before connection could be accepted")


        assert error_server._is_running

    @pytest.mark.parametrize('error_server', [(AttributeError, "accept")], indirect=True)
    def test_mainloop_attribute_error(self, error_server, caplog):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_mainloop_attribute_error.log"),
                         logging.DEBUG,
                         "test_mainloop_attribute_error-filehandler")

        self.assert_msg_logged_mainloop(error_server, caplog, "Server has been stopped")
        self.assert_default_state(error_server)

    @pytest.mark.parametrize('error_server', [(OSError, "accept")], indirect=True)
    def test_mainloop_os_error(self, error_server, dummy_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_mainloop_os_error.log"),
                         logging.DEBUG,
                         "test_mainloop_os_error-filehandler")

        assert error_server.client_count == 0

    """Test message queue"""

    @pytest.mark.parametrize('client_list', [10], indirect=True)
    def test_pop_msg(self, server, client_list):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_pop_msg.log"),
                         logging.DEBUG,
                         "test_pop_msg-filehandler")

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

        with pytest.raises(KeyError):
            server.send("000000000", b"Hello World!")
        assert server.send(client_id, b"Hello World!")

        msg = client.receive()
        assert msg == b"Hello World!"

    def test_on_connect(self, on_connect_server, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_on_connect.log"),
                         logging.DEBUG,
                         "test_on_connect-filehandler")

        on_connect_server.start((HOST, PORT))
        time.sleep(0.1)

        client.connect((HOST, PORT))
        time.sleep(0.1)

        assert on_connect_server.client_count == 0
        client.send(b"H")
        time.sleep(0.1)
        assert not on_connect_server.has_messages()

    def test_invalid_address(self, server_no_start):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_invalid_address.log"),
                         logging.DEBUG,
                         "test_invalid_address-filehandler")


        with pytest.raises(ValueError):
            server_no_start.start(("999.999.999.999", PORT))

        with pytest.raises(ValueError):
            server_no_start.start(("255.255.255.255", PORT))

        with pytest.raises(ValueError):
            server_no_start.start((HOST, 70000))

    def test_start_stop_multiple_calls(self, server, client, caplog):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_reentrant_start_stop.log"),
                         logging.DEBUG,
                         "test_reentrant_start_stop-filehandler")

        server.start((HOST, PORT))
        time.sleep(0.1)
        assert server.is_running
        server.start((HOST, PORT))
        time.sleep(0.1)
        assert server.is_running

        with caplog.at_level(logging.INFO):
            server.stop()
            while server.is_running:
                pass
            server.stop()
            time.sleep(0.1)

        assert len([record for record in caplog.records if "Server has been stopped" in record.msg]) == 1

    def test_client_disconnect_updates_server_state(self, server, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_client_disconnect_updates_server_state.log"),
                         logging.DEBUG,
                         "test_client_disconnect_updates_server_state-filehandler")


        server.start((HOST, PORT))
        time.sleep(0.1)
        client.connect((HOST, PORT))
        time.sleep(0.1)

        assert server.client_count == 1

        client.disconnect()
        time.sleep(0.1)

        assert server.client_count == 0

        server.stop()


