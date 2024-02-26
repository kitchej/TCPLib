import time

from tests.fixtures import dummy_client, dummy_server, server, client, HOST, PORT


def test_server_state(dummy_client, server):
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

    client_info = server.get_client_info(client)

    try:
        assert client_info["is_connected"] is True
        assert client_info["addr"][0] == HOST
        assert client_info["timeout"] is None
    except KeyError:
        assert False

    server.edit_client_prop(client, timeout=10)
    client_info = server.get_client_info(client)

    try:
        assert client_info["is_connected"] is True
        assert client_info["addr"][0] == HOST
        assert client_info["timeout"] == 10
    except KeyError:
        assert False

    server.disconnect_client(client)

    assert server.is_full() is False
    assert server.client_count() == 0

    server.stop()

    assert server.addr() == (HOST, PORT)
    assert server.is_running() is False
    assert server._listener._soc is None


def test_client_state(dummy_server, client):
    assert client.timeout() is None
    assert client.is_connected() is False

    client.connect(HOST, PORT)
    time.sleep(0.1)

    assert client.addr() == (HOST, PORT)
    assert client.is_connected() is True

    client.disconnect()

    assert client.addr() == (HOST, PORT)
    assert client.is_connected() is False
