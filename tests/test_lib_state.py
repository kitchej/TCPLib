import time
import pytest
from tests.globals_for_tests import setup_log_folder, HOST, PORT


class TestLibState:
    log_folder = setup_log_folder("TestLibState")

    @pytest.mark.parametrize('server', [log_folder], indirect=True)
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

    @pytest.mark.parametrize('client', [log_folder], indirect=True)
    @pytest.mark.parametrize('active_client', [log_folder], indirect=True)
    def test_client_state(self, dummy_server, client, active_client):
        # Test PassiveClient state first
        assert client.timeout() is None
        assert client.is_connected() is False

        client.connect()
        time.sleep(0.1)

        assert client.addr() == (HOST, PORT)
        assert client.is_connected() is True

        client.disconnect()

        assert client.addr() == (HOST, PORT)
        assert client.is_connected() is False

        # Test state unique to ActiveClient

        assert not active_client.has_messages()
        assert active_client.id() == active_client._client_id

