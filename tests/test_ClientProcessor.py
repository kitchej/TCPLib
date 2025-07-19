import socket
import time
import logging
import os

import TCPLib.utils as utils
import pytest

from globals_for_tests import setup_log_folder, DUMMY_ID
from log_util import add_file_handler

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_folder = setup_log_folder("TestClientProcessor")


class TestClientProcessor:

    @staticmethod
    def assert_default_state(processor):
        assert processor._client_id == DUMMY_ID
        assert processor._tcp_client is not None
        assert processor._buff_size == 4096
        assert processor._is_running is False

    def recv_loop_raise_exception(self, proc, c):
        try:
            proc.start()
            while not proc.is_running:
                pass
            time.sleep(0.1)
            c.sendall(b"Hello World!")
        except Exception as e:
            assert isinstance(e, c.excep)
            time.sleep(0.1)
            self.assert_default_state(proc)

    def test_class_state(self, client_processor):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_class_state.log"),
                         logging.DEBUG,
                         "test_class_state-filehandler")

        processor = client_processor[0]
        client = client_processor[1]
        self.assert_default_state(processor)
        processor.start()

        while not processor.is_running:
            pass

        time.sleep(0.1)

        assert processor._client_id == DUMMY_ID
        assert processor._tcp_client is not None
        assert processor._buff_size == 4096
        assert processor._is_running is True

        assert processor.id == DUMMY_ID
        try:
            processor.id = " "
        except Exception as e:
            assert isinstance(e, AttributeError)

        assert processor.timeout is None
        processor.timeout = 10
        assert processor.timeout == 10
        processor.timeout = None
        assert processor.timeout is None

        assert processor.remote_addr == client.getsockname()
        try:
            processor.remote_addr = ("111.111.111", 1000)
        except Exception as e:
            assert isinstance(e, AttributeError)

        assert processor.is_running is True
        try:
            processor.is_running = False
        except Exception as e:
            assert isinstance(e, AttributeError)

        processor.stop()
        self.assert_default_state(processor)

    @pytest.mark.parametrize('error_client_processor', [(AttributeError, "recv")], indirect=True)
    def test_recv_loop_raise_AttributeError(self, error_client_processor):
        add_file_handler(logger,
                         os.path.join(log_folder, "raise_AttributeError.log"),
                         logging.DEBUG,
                         "raise_AttributeError-filehandler")

        self.recv_loop_raise_exception(error_client_processor[0], error_client_processor[1])

    @pytest.mark.parametrize('error_client_processor', [(TimeoutError, "recv")], indirect=True)
    def test_recv_loop_raise_TimeoutError(self, error_client_processor):
        add_file_handler(logger,
                         os.path.join(log_folder, "raise_TimeoutError.log"),
                         logging.DEBUG,
                         "raise_TimeoutError-filehandler")

        self.recv_loop_raise_exception(error_client_processor[0], error_client_processor[1])

    @pytest.mark.parametrize('error_client_processor', [(ConnectionError, "recv")], indirect=True)
    def test_recv_loop_raise_ConnectionError(self, error_client_processor):
        add_file_handler(logger,
                         os.path.join(log_folder, "raise_ConnectionError.log"),
                         logging.DEBUG,
                         "raise_ConnectionError-filehandler")

        self.recv_loop_raise_exception(error_client_processor[0], error_client_processor[1])

    @pytest.mark.parametrize('error_client_processor', [(socket.gaierror, "recv")], indirect=True)
    def test_recv_loop_raise_gaierror(self, error_client_processor):
        add_file_handler(logger,
                         os.path.join(log_folder, "raise_gaierror.log"),
                         logging.DEBUG,
                         "raise_gaierror-filehandler")

        self.recv_loop_raise_exception(error_client_processor[0], error_client_processor[1])

    @pytest.mark.parametrize('error_client_processor', [(OSError, "recv")], indirect=True)
    def test_recv_loop_raise_OSError(self, error_client_processor):
        add_file_handler(logger,
                         os.path.join(log_folder, "raise_OSError.log"),
                         logging.DEBUG,
                         "raise_OSError-filehandler")

        self.recv_loop_raise_exception(error_client_processor[0], error_client_processor[1])

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

    """Edge cases"""

    def test_start_called_twice(self, client_processor):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_start_called_twice.log"),
                         logging.DEBUG, "test_start_called_twice-filehandler")
        processor = client_processor[0]
        processor.start()
        first_thread = processor._thread
        processor.start()  # Should not create new thread
        assert processor._thread is first_thread
        processor.stop()

    def test_stop_called_twice(self, client_processor, caplog):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_stop_called_twice.log"),
                         logging.DEBUG, "test_stop_called_twice-filehandler")
        processor = client_processor[0]

        with caplog.at_level(logging.DEBUG):
            processor.start()
            processor.stop()
            processor.stop()

        assert len([record for record in caplog.records if "has been stopped." in record.msg]) == 1



