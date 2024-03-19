"""
test_client_mgmt.py
Written by: Joshua Kitchen - 2024
"""
import pytest
import time

from tests.globals_for_tests import setup_log_folder, HOST, PORT

"""
TO TEST:
- Test that server connection limits are enforced
- Test that clients can be disconnected without crashing the client
- 
"""


class TestClientMgmt:
    log_folder = setup_log_folder("TestClientMgmt")

    @pytest.mark.parametrize('client_list', [[log_folder, 11, "test-server-limits"]], indirect=True)
    @pytest.mark.parametrize('server', [[log_folder, "test-server-limits"]], indirect=True)
    def test_server_limits(self, server, client_list):
        """
        10 clients should connect and the 11th should be denied connection
        """
        server.set_max_clients(10)
        last_client = client_list.pop()

        for client in client_list:
            client.connect()
        time.sleep(0.1)

        assert server.client_count() == 10

        last_client.connect()
        time.sleep(0.1)
        assert not last_client.is_connected()

        for client in server.list_clients():
            server.disconnect_client(client)

        assert server.client_count() == 0

    @pytest.mark.parametrize('client_list', [[log_folder, 11, "test-gen"]], indirect=True)
    @pytest.mark.parametrize('server', [[log_folder, "test-gen"]], indirect=True)
    def test_gen(self, server, client_list):
        assert True
