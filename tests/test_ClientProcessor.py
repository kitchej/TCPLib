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

    @staticmethod
    def recv_loop_raise_exception(proc, caplog, expected_txt, wait_time=2, log_level=logging.DEBUG):
        """
        Starts a ClientProcessor and confirms an injected exception is logged during _receive_loop().

        Parameters:
        proc        -> ClientProcessor instance (e.g., from `error_client_processor` fixture)
        caplog      -> The pytest `caplog` fixture
        expected_txt -> Expected string in the log
        wait_time   -> Max time to wait for log message
        log_level   -> The log level to capture
        """
        with caplog.at_level(log_level):
            proc.start()
            timeout = time.time() + wait_time
            found = False

            while time.time() < timeout:
                if any(expected_txt in record.msg for record in caplog.records):
                    found = True
                    break
                time.sleep(0.05)

            if not found:
                raise AssertionError(f"Could not find expected log message: \"{expected_txt}\"")

    @staticmethod
    def assert_message_logged_recv_loop(proc, expected_txt, caplog, wait_time, log_level=logging.DEBUG):
        """
        Asserts that a message was logged in ClientProcessor._receive_loop()
        Parameters:
        proc -> ClientProcessor to test
        expected_text -> Part or all of the expected log message
        caplog -> the caplog fixture (must be requested in the test)
        log_level -> Specifies which logging level to look for expected_txt in
        """
        with caplog.at_level(log_level):
            proc.start()
            while not proc.is_running:
                continue
            timeout = time.time() + wait_time
            found = False
            while time.time() < timeout:
                if any(expected_txt in record.msg for record in caplog.records):
                    found = True
                    break
                time.sleep(0.05)
            if not found:
                raise AssertionError(f"Could not find \"{expected_txt}\" in logs")

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
        with pytest.raises(AttributeError):
            processor.id = " "

        assert processor.timeout is None
        processor.timeout = 10
        assert processor.timeout == 10
        processor.timeout = None
        assert processor.timeout is None

        assert processor.remote_addr == client.getsockname()
        with pytest.raises(AttributeError):
            processor.remote_addr = ("111.111.111", 1000)

        assert processor.is_running is True
        with pytest.raises(AttributeError):
            processor.is_running = False

        processor.stop()
        self.assert_default_state(processor)

    """Test error handling in _receive_loop"""

    @pytest.mark.parametrize('error_client_processor', [(AttributeError, "recv")], indirect=True)
    def test_recv_loop_raise_attribute_error(self, error_client_processor, caplog):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_loop_raise_attribute_error.log"),
                         logging.DEBUG,
                         "test_recv_loop_raise_attribute_error-filehandler")

        self.recv_loop_raise_exception(error_client_processor[0], caplog,
                                       "Socket was closed during receive loop")

    def test_recv_loop_raise_timeout_error(self, client_processor, caplog):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_loop_raise_timeout_error.log"),
                         logging.DEBUG,
                         "test_recv_loop_raise_timeout_error-filehandler")

        proc = client_processor[0]
        proc.timeout = 0.5

        self.assert_message_logged_recv_loop(proc,
                                             "Timed out while receiving from",
                                             caplog,
                                             wait_time=2,
                                             log_level=logging.WARNING)

    def test_recv_loop_zero_max_timeouts(self, client_processor, caplog):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_loop_raise_timeout_error.log"),
                         logging.DEBUG,
                         "test_recv_loop_raise_timeout_error-filehandler")

        proc = client_processor[0]
        proc.timeout = 0.5
        proc.max_timeouts = 0

        self.assert_message_logged_recv_loop(proc,
                                             "timed out too many times. Disconnecting.",
                                             caplog,
                                             wait_time=2,
                                             log_level=logging.ERROR)

    def test_recv_loop_too_many_timeouts(self, client_processor, caplog):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_loop_raise_timeout_error.log"),
                         logging.DEBUG,
                         "test_recv_loop_raise_timeout_error-filehandler")

        proc = client_processor[0]
        proc.timeout = 0.5
        proc.max_timeouts = 4

        self.assert_message_logged_recv_loop(proc,
                                             "timed out too many times. Disconnecting.",
                                             caplog,
                                             wait_time=5,
                                             log_level=logging.ERROR)

        assert proc._total_timeouts == 4

    @pytest.mark.parametrize('error_client_processor', [(TimeoutError, "recv")], indirect=True)
    def test_recv_loop_timeouts_reset(self, error_client_processor, caplog):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_loop_raise_timeout_error.log"),
                         logging.DEBUG,
                         "test_recv_loop_raise_timeout_error-filehandler")

        proc = error_client_processor[0]
        err_c = error_client_processor[1]
        proc.timeout = 0.5
        proc.max_timeouts = 5

        proc.start()
        while not proc.is_running:
            pass
        time.sleep(0.1)
        self.recv_loop_raise_exception(proc, err_c)
        time.sleep(0.1)
        self.recv_loop_raise_exception(proc, err_c)
        time.sleep(0.1)
        self.recv_loop_raise_exception(proc, err_c)
        time.sleep(0.1)
        self.recv_loop_raise_exception(proc, err_c)

        with proc._total_timeouts_lock:
            assert proc._total_timeouts == 4

    @pytest.mark.parametrize('error_client_processor', [(ConnectionError, "recv")], indirect=True)
    def test_recv_loop_raise_connection_error(self, error_client_processor):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_loop_raise_connection_error.log"),
                         logging.DEBUG,
                         "test_recv_loop_raise_connection_error-filehandler")

        self.recv_loop_raise_exception(error_client_processor[0], error_client_processor[1])

    @pytest.mark.parametrize('error_client_processor', [(socket.gaierror, "recv")], indirect=True)
    def test_recv_loop_raise_gai_error(self, error_client_processor):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_loop_raise_gai_error.log"),
                         logging.DEBUG,
                         "test_recv_loop_raise_gai_error-filehandler")

        error_client_processor[0].start()
        self.recv_loop_raise_exception(error_client_processor[0], error_client_processor[1])

    @pytest.mark.parametrize('error_client_processor', [(OSError, "recv")], indirect=True)
    def test_recv_loop_raise_os_error(self, error_client_processor):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_loop_raise_os_error.log"),
                         logging.DEBUG,
                         "test_recv_loop_raise_os_error-filehandler")

        error_client_processor[0].start()
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
