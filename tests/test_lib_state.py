"""
TEST STATE SERVER
    - addr
    - is_running
    - client_count
    - is_full
    - max_clients
    - set_max_clients
    - list_clients
    - edit_client_prop
    - get_client_info

TEST STATE TCP_OBJ
    - encode_msg
    - decode_header
    - is_connected
    - default_buff_size
    - set_default_buff_size
    - timeout
    - set_timeout
    - addr
"""
import time

from tests.fixtures import dummy_client, dummy_server, server, client, HOST, PORT


def test_server_state(dummy_client, server):
    assert server.addr() == (HOST, PORT)
    assert server.is_running() is True
    assert server.is_full() is False
    assert server.max_clients() == 0
    assert server.default_buff_size() == 4096

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
        assert client_info["buff_size"] == 4096
    except KeyError:
        assert False

    server.edit_client_prop(client, timeout=10, buff_size=2048)
    client_info = server.get_client_info(client)

    try:
        assert client_info["is_connected"] is True
        assert client_info["addr"][0] == HOST
        assert client_info["timeout"] == 10
        assert client_info["buff_size"] == 2048
    except KeyError:
        assert False

    server.disconnect_client(client)

    assert server.is_full() is False
    assert server.client_count() == 0

    server.close()

    assert server.addr() == (HOST, PORT)
    assert server.is_running() is False
    assert server._listener._soc is None
    assert server.default_buff_size() == 4096


def test_client_state(dummy_server, client):
    assert client.timeout() is None
    assert client.buff_size() == 4096
    assert client.is_connected() is False
    assert client.query_progress() is False

    client.connect(HOST, PORT)
    time.sleep(0.1)

    assert client.addr() == (HOST, PORT)
    assert client.is_connected() is True

    client.disconnect()

    assert client.addr() == (HOST, PORT)
    assert client.is_connected() is False
