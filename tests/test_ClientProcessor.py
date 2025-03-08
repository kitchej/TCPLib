import time
import logging
import os

import TCPLib.utils as utils

from globals_for_tests import setup_log_folder, DUMMY_ID
from log_util import add_file_handler

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_folder = setup_log_folder("TestClientProcessor")


class TestClientProcessor:
    def test_class_state(self, client_processor):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_class_state.log"),
                         logging.DEBUG,
                         "test_class_state-filehandler")
        processor = client_processor[0]
        assert processor._client_id == DUMMY_ID
        assert processor._tcp_client is not None
        assert processor._buff_size == 4096
        assert processor._is_running is False

        processor.start()

        assert processor._client_id == DUMMY_ID
        assert processor._tcp_client is not None
        assert processor._buff_size == 4096
        assert processor._is_running is True

        assert processor.id == DUMMY_ID
        processor.id = " "
        assert processor.id == DUMMY_ID

        assert processor.timeout is None
        processor.timeout = 10
        assert processor.timeout == 10
        processor.timeout = None
        assert processor.timeout is None

        remote_addr = processor._tcp_client.host_addr
        assert processor.remote_addr == remote_addr
        processor.remote_addr = ("111.111.111", 1000)
        assert processor.remote_addr == remote_addr

        assert  processor.is_running is True
        processor.is_running = False
        assert processor.is_running is True

        processor.stop()
        assert processor._client_id == DUMMY_ID
        assert processor._tcp_client is not None
        assert processor._buff_size == 4096
        assert processor._is_running is False


    def test_recv_loop(self, client_processor):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_loop.log"),
                         logging.DEBUG,
                         "test_recv_loop-filehandler")
        processor = client_processor[0]
        client = client_processor[1]
        processor.start()
        q = processor._msg_q

        client.sendall(utils.encode_msg(b'Message 1'))
        client.sendall(utils.encode_msg(b'Message 2'))
        client.sendall(utils.encode_msg(b'Message 3'))

        time.sleep(0.1)

        msg1 = q.get()
        msg2 = q.get()
        msg3 = q.get()

        assert msg1.data == b'Message 1'
        assert msg1.client_id == DUMMY_ID

        assert msg2.data == b'Message 2'
        assert msg2.client_id == DUMMY_ID

        assert msg3.data == b'Message 3'
        assert msg3.client_id == DUMMY_ID

    def test_send(self, client_processor):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send.log"),
                         logging.DEBUG,
                         "test_send-filehandler")

        processor = client_processor[0]
        client = client_processor[1]

        processor.start()

        processor.send(b'Message 1')
        _header = client.recv(4)
        client_cpy = client.recv(1024)
        assert client_cpy == b'Message 1'
