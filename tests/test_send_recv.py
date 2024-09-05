"""
test_send_recv.py
Written by: Joshua Kitchen - 2024
"""
import queue
import time
import pytest
import os
import logging
import threading

from tests.globals_for_tests import setup_log_folder
from dev_tools.log_util import add_file_handler


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_folder = setup_log_folder("TestSendRecv")


class TestSendRecv:
    @staticmethod
    def send(client, thread_id, data, completed_q):
        client.send(data)
        completed_q.put(f"{thread_id} SENT")

    @staticmethod
    def echo(client, server, data):
        time.sleep(0.1)
        server_client_id = server.list_clients()[0]

        client.send(data)

        server_copy = server.pop_msg(block=True)
        server.send(server_client_id, server_copy.data)

        client_copy = client.pop_msg(block=True)

        return server_copy, client_copy

    def test_send_file(self, server, active_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send_file.log"),
                         logging.DEBUG,
                         "test_send_file-filehandler")
        with open(os.path.abspath(os.path.join("dummy_files", "video1.mkv")), 'rb') as file:
            video = file.read()

        server.start()
        time.sleep(0.1)
        active_client.start()
        time.sleep(0.1)
        server_client_id = server.list_clients()[0]
        server_msg, client_msg = self.echo(active_client, server, video)

        assert server_msg.size == len(video)
        assert server_msg.flags == 2
        assert server_msg.data == video
        assert server_msg.client_id == server_client_id

        assert client_msg.size == len(video)
        assert client_msg.flags == 2
        assert client_msg.data == video

        active_client.stop(warn=True)
        time.sleep(0.1)
        server.stop()

    @pytest.mark.parametrize('client_list', [20], indirect=True)
    def test_send_file_multi_client(self, client_list, server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send_file_multi_client.log"),
                         logging.DEBUG,
                         "test_send_file_multi_client-filehandler")
        with open(os.path.abspath(os.path.join("dummy_files", "photo.jpg")), 'rb') as file:
            photo = file.read()

        completed = queue.Queue()

        server.start()
        time.sleep(0.1)
        threads = []
        for i, c in enumerate(client_list):
            c.connect()
            threads.append(threading.Thread(target=self.send, args=[c, i, photo, completed]))

        for thread in threads:
            thread.start()

        # Wait for all msgs to be sent
        for i in range(20):
            completed.get(block=True)

        assert server.has_messages()

        for msg in server.get_all_msg():
            assert msg.data == photo
