import time
import logging
import os

from tests.globals_for_tests import setup_log_folder, HOST, PORT
from src.log_util import add_file_handler

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_folder = setup_log_folder("TestLibState")


class TestLibState:
    def test_server_state(self, dummy_client, server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_server_state.log"),
                         logging.DEBUG,
                         "test_server_state-filehandler")

        assert server.addr() == (HOST, PORT)
        assert not server.is_running()
        assert not server.is_full()
        assert server.max_clients() == 0
        assert server.server_timeout() is None

        server.set_addr("123.456.789", 9000)
        assert server.addr() == ("123.456.789", 9000)
        server.set_addr(HOST, PORT)
        assert server.addr() == (HOST, PORT)

        server.start()
        time.sleep(0.1)

        server.set_addr("123.456.789", 9000)
        assert server.addr() == (HOST, PORT)
        assert server.is_running()
        assert not server.is_full()
        assert server.max_clients() == 0
        assert server.server_timeout() is None

        assert server.set_server_timeout(10)
        assert server.server_timeout() == 10
        assert not server.set_server_timeout(-1)
        assert not server.set_server_timeout(-25)
        assert server.server_timeout() == 10
        assert server.set_server_timeout(None)

        assert server.set_max_clients(1)
        assert server.max_clients() == 1
        assert not server.set_max_clients(-1)
        assert not server.set_max_clients(-25)
        assert server.max_clients() == 1

        dummy_client.connect((HOST, PORT))
        time.sleep(0.1)
        assert server.client_count() == 1
        assert server.is_full() is True

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

        assert server.is_full() is False
        assert server.client_count() == 0

        server.stop()

        assert server.addr() == (HOST, PORT)
        assert not server.is_running()
        assert not server.is_full()
        assert server.max_clients() == 1

    def test_client_state(self, dummy_server, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_passive_client_state.log"),
                         logging.DEBUG,
                         "test_passive_client_state-filehandler")
        assert client.timeout() is None
        assert client.is_connected() is False

        client.set_timeout(10)
        assert client.timeout() == 10

        client.set_addr("123.456.789", 9000)
        assert client.addr() == ("123.456.789", 9000)
        client.set_addr(HOST, PORT)
        assert client.addr() == (HOST, PORT)

        assert client.connect() is True
        time.sleep(0.1)

        assert client.is_connected() is True
        client.set_addr(HOST, PORT)
        assert client.addr() == (HOST, PORT)

        client.disconnect()

        assert client.addr() == (HOST, PORT)
        assert client.is_connected() is False

    def test_auto_client_state(self, dummy_server, active_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_active_client_state.log"),
                         logging.DEBUG,
                         "test_active_client_state-filehandler")
        assert not active_client.has_messages()
        assert active_client.id() == active_client._client_id
        assert active_client.addr() == (HOST, PORT)
        assert active_client.timeout() is None
        assert active_client.is_running() is False

        active_client.set_timeout(10)
        assert active_client.timeout() == 10

        active_client.set_addr("123.456.789", 9000)
        assert active_client.addr() == ("123.456.789", 9000)
        active_client.set_addr(HOST, PORT)
        assert active_client.addr() == (HOST, PORT)

        assert active_client.start() is True
        time.sleep(0.1)

        assert active_client.is_running() is True
        active_client.set_addr("123.456.789", 9000)
        assert active_client.addr() == (HOST, PORT)

        active_client._msg_queue.put("Hello World")
        active_client._msg_queue.put("Hello World1")
        active_client._msg_queue.put("Hello World2")

        assert active_client.has_messages()
        msg0 = active_client.pop_msg()

        assert msg0 == "Hello World"

        remaining_msgs = [msg for msg in active_client.get_all_msg()]

        assert len(remaining_msgs) == 2
        assert remaining_msgs[0] == "Hello World1"
        assert remaining_msgs[1] == "Hello World2"
