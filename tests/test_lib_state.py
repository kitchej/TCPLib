import time
import pytest
from tests.globals_for_tests import setup_log_folder, HOST, PORT


class TestLibState:
    log_folder = setup_log_folder("TestLibState")

    @pytest.mark.parametrize('server', [[log_folder, "test-server-state"]], indirect=True)
    def test_server_state(self, dummy_client, server):
        assert server.addr() == (HOST, PORT)
        assert server.is_running() is True
        assert server.is_full() is False
        assert server.max_clients() == 0

        assert server.listener_timeout() is None
        server.set_listener_timeout(10)
        assert server.listener_timeout() == 10
        server.set_listener_timeout(None)

        server.set_max_clients(1)
        assert server.max_clients() == 1

        dummy_client.connect((HOST, PORT))
        time.sleep(0.1)
        assert server.client_count() == 1
        assert server.is_full() is True

        assert server.list_clients()
        client = server.list_clients()[0]

        client_proc = server._get_client(client)
        client_info = server.get_client_info(client)

        try:
            assert client_info["is_running"] is True
            assert client_info["host"] == HOST
            assert client_info["port"] == client_proc._tcp_client._addr[1]
        except KeyError:
            assert False

        server.disconnect_client(client)

        assert server.is_full() is False
        assert server.client_count() == 0

        server.stop()

        assert server.addr() == (HOST, PORT)
        assert server.is_running() is False
        assert server._listener._soc is None

    @pytest.mark.parametrize('client', [[log_folder, "test-passive-client-state"]], indirect=True)
    def test_passive_client_state(self, dummy_server, client):
        assert client.timeout() is None
        assert client.is_connected() is False

        client.set_timeout(10)
        assert client.timeout() == 10

        client.connect()
        time.sleep(0.1)

        assert client.addr() == (HOST, PORT)
        assert client.is_connected() is True

        client.disconnect()

        assert client.addr() == (HOST, PORT)
        assert client.is_connected() is False

    @pytest.mark.parametrize('active_client', [[log_folder, "test-active-client-state"]], indirect=True)
    def test_active_client_state(self, dummy_server, active_client):
        assert not active_client.has_messages()
        assert active_client.id() == active_client._client_id
        assert active_client.addr() == (HOST, PORT)
        assert active_client.timeout() is None
        time.sleep(0.1)  # For some reason if this isn't here, the below assertion will fail
        assert active_client.is_running() is False

        active_client.set_timeout(10)
        assert active_client.timeout() == 10

        active_client.start()
        time.sleep(0.1)

        assert active_client.is_running() is True

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
