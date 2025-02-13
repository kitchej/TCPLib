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
from src.log_util import add_file_handler


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
        client.send(data)
        time.sleep(0.1)
        server_copy = server.pop_msg(block=True)
        server.send(server_copy.client_id, server_copy.data)
        client_copy = client.receive()
        return server_copy, client_copy

    def test_send_file(self, server, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send_file.log"),
                         logging.DEBUG,
                         "test_send_file-filehandler")
        with open(os.path.abspath(os.path.join("dummy_files", "video1.mkv")), 'rb') as file:
            video = file.read()

        server.start()
        time.sleep(0.1)
        client.connect()
        time.sleep(0.1)
        server_client_id = server.list_clients()[0]
        server_msg, client_msg = self.echo(client, server, video)

        assert server_msg.size == len(video)
        assert server_msg.data == video
        assert server_msg.client_id == server_client_id

        assert len(client_msg) == len(video)
        assert client_msg == video

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

    @pytest.mark.parametrize('client_list', [2], indirect=True)
    def test_client_to_client_recv(self, client_list):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_client_to_client_recv.log"),
                         logging.DEBUG,
                         "test_client_to_client_recv-filehandler")

        with open(os.path.abspath(os.path.join("dummy_files", "video1.mkv")), 'rb') as file:
            video = file.read()

        client1 = client_list[0]
        client2 = client_list[1]

        threading.Thread(target=client1.single_client_connect).start()
        time.sleep(0.1)
        client2.connect()
        time.sleep(0.1)

        client1.send(b'Hello World')
        client2_cpy = client2.receive()
        client2.send(client2_cpy)
        client1_cpy = client1.receive()

        assert client1_cpy == client2_cpy

        client1.send(video)
        client2_cpy = client2.receive()
        client2.send(client2_cpy)
        client1_cpy = client1.receive()

        assert client1_cpy == client2_cpy
