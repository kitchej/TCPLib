"""
test_client_mgmt.py
Written by: Joshua Kitchen - 2024
"""
import pytest
import time
import logging
import os

from tests.globals_for_tests import setup_log_folder
from src.dev_tools.logger import change_log_path

"""
TO TEST:
- Test that server connection limits are enforced
- Test that clients can be disconnected without crashing the client
- 
"""

logger = logging.getLogger()
log_folder = setup_log_folder("TestClientMgmt")


class TestClientMgmt:

    @pytest.mark.parametrize('client_list', [11], indirect=True)
    def test_server_limits(self, server, client_list):
        """
        10 clients should connect and the 11th should be denied connection
        """
        change_log_path(logger, os.path.join(log_folder, "test_server_limits.log"), logging.DEBUG)
        server.set_max_clients(10)
        last_client = client_list.pop()

        server.start()
        time.sleep(0.1)

        for client in client_list:
            client.connect()
        time.sleep(0.1)

        assert server.client_count() == 10

        last_client.connect()
        time.sleep(0.1)
        assert not last_client.is_connected()
