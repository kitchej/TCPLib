import queue
import time
import logging
import os
import pytest

from globals_for_tests import setup_log_folder, HOST, PORT
from log_util import add_file_handler

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














