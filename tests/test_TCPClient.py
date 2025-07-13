import threading
import time
import logging
import os
import socket
import pytest

from globals_for_tests import setup_log_folder, HOST, PORT
from log_util import add_file_handler
from TCPLib.tcp_client import TCPClient
from TCPLib.utils import encode_msg

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_folder = setup_log_folder("TestTCPClient")


class TestTCPClient:

    @staticmethod
    def assert_default_state(c):
        assert c._soc is None
        assert c._listen_soc is None
        assert c._peer_addr is None
        assert c._local_addr is None
        assert c._timeout is None
        assert c._is_connected is False
        assert c._is_host is False

    @staticmethod
    def assert_excep_raised_on_connect(c, excep):
        try:
            c.connect((HOST, PORT))
        except Exception as e:
            assert isinstance(e, excep)

    @staticmethod
    def assert_excep_raised_on_send(c, excep):
        c.connect((HOST, PORT))
        try:
            c.send(b"Hello World!")
        except Exception as e:
            assert isinstance(e, excep)

    @staticmethod
    def assert_excep_raised_on_recv(c, excep):
        c.connect((HOST, PORT))
        try:
            c.receive()
        except Exception as e:
            assert isinstance(e, excep)

    def test_class_state(self, client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_class_state.log"),
                         logging.DEBUG,
                         "test_class_state-filehandler")
        dummy_server.start()

        self.assert_default_state(client)

        client.connect((HOST, PORT))

        assert isinstance(client._soc, socket.socket)
        assert client._listen_soc is None
        assert client._local_addr is not None
        assert client._peer_addr == (HOST, PORT)
        assert client._timeout is None
        assert client._is_connected is True
        assert client._is_host is False

        assert client.is_connected
        try:
            client.is_connected = False
        except Exception as e:
            assert isinstance(e, AttributeError)
        assert client.is_connected

        assert client.timeout is None
        client.timeout = 10
        assert client.timeout == 10
        assert client._soc.timeout == 10
        client.timeout = None

        assert client.peer_addr == (HOST, PORT)
        try:
            client.peer_addr = ("192.168.010", 6000)
        except Exception as e:
            assert isinstance(e, AttributeError)
        assert client.peer_addr == (HOST, PORT)

        assert client.is_host is False
        try:
            client.is_host = True
        except Exception as e:
            assert isinstance(e, AttributeError)
        assert client.is_host is False

        client.disconnect()
        self.assert_default_state(client)

    def test_from_socket(self, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_from_socket.log"),
                         logging.DEBUG,
                         "test_from_socket-filehandler")
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dummy_server.start()
        soc.connect((HOST, PORT))
        c = TCPClient.from_socket(soc)

        assert isinstance(c._soc, socket.socket)
        assert c._listen_soc is None
        assert c._local_addr is not None
        assert c._peer_addr == (HOST, PORT)
        assert c._timeout is None
        assert c._is_connected is True
        assert c._is_host is False

        c.disconnect()

    def test_host_single_client(self, client, dummy_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_host_single_client.log"),
                         logging.DEBUG,
                         "test_host_single_client-filehandler")
        self.assert_default_state(client)

        try:
            client.host_single_client((HOST, PORT), timeout=0.1)
        except Exception as e:
            assert isinstance(e, TimeoutError)

        threading.Thread(target=client.host_single_client, args=[(HOST, PORT), 5]).start()
        time.sleep(0.1)
        dummy_client.connect((HOST, PORT))
        time.sleep(0.1)

        assert isinstance(client._soc, socket.socket)
        assert client._listen_soc is None
        assert client._peer_addr == dummy_client.getsockname()
        assert client._local_addr == (HOST, PORT)
        assert client._timeout is None
        assert client._is_connected is True
        assert client._is_host is True

        client.disconnect()
        self.assert_default_state(client)

    """Test exceptions in TCPClient.connect()"""

    @pytest.mark.parametrize('error_client', [(TimeoutError, "connect")], indirect=True)
    def test_connect_timeout_error(self, error_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_connect_timeout_error.log"),
                         logging.DEBUG,
                         "test_connect_timeout_error-filehandler")

        self.assert_excep_raised_on_connect(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    @pytest.mark.parametrize('error_client', [(ConnectionError, "connect")], indirect=True)
    def test_connect_connection_error(self, error_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_connect_connection_error.log"),
                         logging.DEBUG,
                         "test_connect_connection_error-filehandler")

        self.assert_excep_raised_on_connect(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    @pytest.mark.parametrize('error_client', [(socket.gaierror, "connect")], indirect=True)
    def test_connect_gai_error(self, error_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_connect_gai_error.log"),
                         logging.DEBUG,
                         "test_connect_gai_error-filehandler")

        self.assert_excep_raised_on_connect(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    @pytest.mark.parametrize('error_client', [(OSError, "connect")], indirect=True)
    def test_connect_os_error(self, error_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_connect_os_error.log"),
                         logging.DEBUG,
                         "test_connect_os_error-filehandler")

        self.assert_excep_raised_on_connect(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    """Test exceptions in TCPClient.send()"""

    @pytest.mark.parametrize('error_client', [(AttributeError, "sendall")], indirect=True)
    def test_send_attribute_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send_attribute_error.log"),
                         logging.DEBUG,
                         "test_send_attribute_error-filehandler")

        dummy_server.start()

        self.assert_excep_raised_on_send(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    @pytest.mark.parametrize('error_client', [(TimeoutError, "sendall")], indirect=True)
    def test_send_timeout_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send_timeout_error.log"),
                         logging.DEBUG,
                         "test_send_timeout_error-filehandler")

        dummy_server.start()

        self.assert_excep_raised_on_send(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    @pytest.mark.parametrize('error_client', [(ConnectionError, "sendall")], indirect=True)
    def test_send_connection_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send_connection_error.log"),
                         logging.DEBUG,
                         "test_send_connection_error-filehandler")

        dummy_server.start()

        self.assert_excep_raised_on_send(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    @pytest.mark.parametrize('error_client', [(OSError, "sendall")], indirect=True)
    def test_send_os_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send_os_error.log"),
                         logging.DEBUG,
                         "test_send_os_error-filehandler")

        dummy_server.start()

        self.assert_excep_raised_on_send(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    @pytest.mark.parametrize('error_client', [(AttributeError, "recv")], indirect=True)
    def test_recv_attribute_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_attribute_error.log"),
                         logging.DEBUG,
                         "test_recv_attribute_error-filehandler")

        dummy_server.start()

        self.assert_excep_raised_on_recv(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    @pytest.mark.parametrize('error_client', [(TimeoutError, "recv")], indirect=True)
    def test_recv_timeout_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_timeout_error.log"),
                         logging.DEBUG,
                         "test_recv_timeout_error-filehandler")

        dummy_server.start()

        self.assert_excep_raised_on_recv(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    @pytest.mark.parametrize('error_client', [(ConnectionError, "recv")], indirect=True)
    def test_recv_connection_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_connection_error.log"),
                         logging.DEBUG,
                         "test_recv_connection_error-filehandler")

        dummy_server.start()

        self.assert_excep_raised_on_recv(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    @pytest.mark.parametrize('error_client', [(OSError, "recv")], indirect=True)
    def test_recv_os_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_os_error.log"),
                         logging.DEBUG,
                         "test_recv_os_error-filehandler")

        dummy_server.start()

        self.assert_excep_raised_on_recv(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    """Test send/recv functionality"""

    def test_send(self, client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_os_error.log"),
                         logging.DEBUG,
                         "test_recv_os_error-filehandler")

        msg1 = b"Hello World!"
        msg2 = b"foofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoo"
        with open("tests/dummy_files/doi.txt", 'rb') as file:
            text = file.read()

        dummy_server.start()
        client.connect((HOST, PORT))

        client.send(msg1)
        time.sleep(0.1)
        _ = dummy_server.soc.recv(4)
        server_cpy = dummy_server.soc.recv(1024)
        assert server_cpy == msg1

        client.send(msg2)
        time.sleep(0.1)
        _ = dummy_server.soc.recv(4)
        server_cpy = dummy_server.soc.recv(1024)
        assert server_cpy == msg2

        client.send(text)
        time.sleep(0.1)
        _ = dummy_server.soc.recv(4)
        server_cpy = dummy_server.soc.recv(len(text))
        assert server_cpy == text

    def test_recv_chunk(self, client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_chunk.log"),
                         logging.DEBUG,
                         "test_recv_chunk-filehandler")

        dummy_server.start()
        client.connect((HOST, PORT))
        time.sleep(0.1)

        dummy_server.send(b"Hello World!")
        time.sleep(0.1)
        data = client.receive_bytes(4)
        assert len(data) == 4

        dummy_server.send(b"Hello World!")
        time.sleep(0.1)
        data = client.receive_bytes(12)
        assert len(data) == 12

    def test_iter_receive(self, client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_iter_receive.log"),
                         logging.DEBUG,
                         "test_iter_receive-filehandler")

        msg = b"Hello World!"
        dummy_server.start()
        client.connect((HOST, PORT))
        time.sleep(0.1)

        dummy_server.send(encode_msg(msg))
        time.sleep(0.1)
        gen = client.iter_receive(1)

        size = next(gen)
        assert size == len(msg)

        for char in msg:
            assert chr(char) == str(next(gen), encoding='utf-8')

    def test_receive(self, client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_receive.log"),
                         logging.DEBUG,
                         "test_receive-filehandler")

        msg1 = b"Hello World!"
        msg2 = b"H"
        with open("tests/dummy_files/doi.txt", 'rb') as file:
            text = file.read()

        dummy_server.start()
        client.connect((HOST, PORT))
        time.sleep(0.1)

        dummy_server.send(encode_msg(msg1))
        time.sleep(0.1)
        assert client.receive() == msg1

        dummy_server.send(encode_msg(msg2))
        time.sleep(0.1)
        assert client.receive() == msg2

        dummy_server.send(encode_msg(text))
        time.sleep(0.1)
        assert client.receive() == text

    def test_receive_multimedia(self, client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_receive_multimedia.log"),
                         logging.DEBUG,
                         "test_receive_multimedia-filehandler")

        with open("tests/dummy_files/video1.mkv", 'rb') as file:
            video = file.read()

        with open("tests/dummy_files/photo.jpg", 'rb') as file:
            photo = file.read()

        dummy_server.start()
        client.connect((HOST, PORT))
        time.sleep(0.1)

        dummy_server.send(encode_msg(photo))
        time.sleep(0.1)
        assert client.receive() == photo

        dummy_server.send(encode_msg(video))
        time.sleep(0.1)
        assert client.receive() == video

    def test_context_manager(self, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_context_manager.log"),
                         logging.DEBUG,
                         "test_context_manager-filehandler")

        dummy_server.start()
        threading.Thread(target=lambda: dummy_server.soc.recv(1024)).start()
        with TCPClient() as client:
            client.connect((HOST, PORT))
            time.sleep(0.1)
            assert client.is_connected
            client.send(b"Hello World!")
            time.sleep(0.1)

        assert client.is_connected is False