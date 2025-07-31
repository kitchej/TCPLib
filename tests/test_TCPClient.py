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
        with pytest.raises(excep):
            c.connect((HOST, PORT))

    @staticmethod
    def assert_excep_raised_on_reconnect(c, excep):
        with pytest.raises(excep):
            c.reconnect()

    @staticmethod
    def assert_excep_raised_on_send(c, excep):
        c.connect((HOST, PORT))
        with pytest.raises(excep):
            c.send(b"Hello World!")

    @staticmethod
    def assert_excep_raised_on_recv(c, excep):
        c.connect((HOST, PORT))
        with pytest.raises(excep):
            c.receive()

    @staticmethod
    def assert_excep_raised_on_host_single_client(c, excep):
        with pytest.raises(excep):
            c.host_single_client((HOST, PORT), 5)

    def test_class_state(self, client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_class_state.log"),
                         logging.DEBUG,
                         "test_class_state-filehandler")
        dummy_server.start((HOST, PORT))

        self.assert_default_state(client)

        client.connect((HOST, PORT))

        assert isinstance(client._soc, socket.socket)
        assert client._listen_soc is None
        assert client._local_addr is not None
        assert client._peer_addr == (HOST, PORT)
        assert client._timeout is None
        assert client._is_connected
        assert client._is_host is False

        with pytest.raises(AttributeError):
            client.is_connected = False

        assert client.is_connected

        assert client.timeout is None
        client.timeout = 10
        assert client.timeout == 10
        assert client._soc.timeout == 10
        client.timeout = None

        assert client.peer_addr == (HOST, PORT)
        with pytest.raises(AttributeError):
            client.peer_addr = ("192.168.010", 6000)
        assert client.peer_addr == (HOST, PORT)

        assert client.is_host is False
        with pytest.raises(AttributeError):
            client.is_host = True
        assert client.is_host is False

        client.disconnect()
        self.assert_default_state(client)

    def test_from_socket(self, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_from_socket.log"),
                         logging.DEBUG,
                         "test_from_socket-filehandler")
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dummy_server.start((HOST, PORT))
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

        with pytest.raises(TimeoutError):
            client.host_single_client((HOST, PORT), timeout=0.1)

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

    def test_from_socket_listen_socket(self, dummy_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_from_socket_listen_socket.log"),
                         logging.DEBUG,
                         "test_from_socket_listen_socket-filehandler")

        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client = TCPClient.from_socket(soc, is_listen_soc=True)
        assert client._listen_soc is not None
        assert client._soc is None
        assert client._peer_addr is None
        assert client._local_addr is None
        assert client._timeout is None
        assert client._is_connected is False
        assert client._is_host

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

        dummy_client.close()
        client.disconnect()

    def test_reconnect(self, dummy_server, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_reconnect.log"),
                         logging.DEBUG,
                         "test_reconnect-filehandler")

        with pytest.raises(ConnectionError) as exc_info:
            client.reconnect()

        assert "No previous connection available to reconnect to" in exc_info.__str__()

        dummy_server.start((HOST, PORT))
        client.connect((HOST, PORT))
        time.sleep(0.1)
        assert client.is_connected
        client.disconnect()
        assert not client.is_connected
        dummy_server.stop()

        dummy_server.start((HOST, PORT))
        client.reconnect()
        assert client.is_connected

    """Test exceptions in reconnect"""

    @pytest.mark.parametrize('error_reconnect_client', [(TimeoutError, "connect")], indirect=True)
    def test_reconnect_timeout_error(self, error_reconnect_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_reconnect_timeout_error.log"),
                         logging.DEBUG,
                         "test_reconnect_timeout_error-filehandler")

        self.assert_excep_raised_on_reconnect(error_reconnect_client, error_reconnect_client._soc.excep)
        self.assert_default_state(error_reconnect_client)

    @pytest.mark.parametrize('error_reconnect_client', [(ConnectionError, "connect")], indirect=True)
    def test_reconnect_connection_error(self, error_reconnect_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_reconnect_connection_error.log"),
                         logging.DEBUG,
                         "test_reconnect_connection_error-filehandler")

        self.assert_excep_raised_on_reconnect(error_reconnect_client, error_reconnect_client._soc.excep)
        self.assert_default_state(error_reconnect_client)

    @pytest.mark.parametrize('error_reconnect_client', [(OSError, "connect")], indirect=True)
    def test_reconnect_os_error(self, error_reconnect_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_reconnect_os_error.log"),
                         logging.DEBUG,
                         "test_reconnect_os_error-filehandler")

        self.assert_excep_raised_on_reconnect(error_reconnect_client, error_reconnect_client._soc.excep)
        self.assert_default_state(error_reconnect_client)

    @pytest.mark.parametrize('error_reconnect_client', [(socket.gaierror, "connect")], indirect=True)
    def test_reconnect_gai_error(self, error_reconnect_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_reconnect_gai_error.log"),
                         logging.DEBUG,
                         "test_reconnect_gai_error-filehandler")

        self.assert_excep_raised_on_reconnect(error_reconnect_client, error_reconnect_client._soc.excep)
        self.assert_default_state(error_reconnect_client)


    """Test exceptions in TCPClient.host_single_client()"""

    @pytest.mark.parametrize('error_host_client', [(socket.gaierror, "bind")], indirect=True)
    def test_host_single_client_gai_error(self, error_host_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_host_single_client_gai_error.log"),
                         logging.DEBUG,
                         "test_host_single_client_gai_error-filehandler")

        self.assert_excep_raised_on_host_single_client(error_host_client, error_host_client._listen_soc.excep)
        self.assert_default_state(error_host_client)

    @pytest.mark.parametrize('error_host_client', [(OSError, "bind")], indirect=True)
    def test_host_single_client_os_error(self, error_host_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_host_single_client_os_error.log"),
                         logging.DEBUG,
                         "test_host_single_client_os_error-filehandler")

        self.assert_excep_raised_on_host_single_client(error_host_client, error_host_client._listen_soc.excep)
        self.assert_default_state(error_host_client)

    @pytest.mark.parametrize('error_host_client', [(TimeoutError, "listen")], indirect=True)
    def test_host_single_client_timeout_error(self, error_host_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_host_single_client_timeout_error.log"),
                         logging.DEBUG,
                         "test_host_single_client_timeout_error-filehandler")

        self.assert_excep_raised_on_host_single_client(error_host_client, error_host_client._listen_soc.excep)
        self.assert_default_state(error_host_client)

    @pytest.mark.parametrize('error_host_client', [(ConnectionError, "listen")], indirect=True)
    def test_host_single_client_connection_error(self, error_host_client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_host_single_client_connection_error.log"),
                         logging.DEBUG,
                         "test_host_single_client_connection_error-filehandler")

        self.assert_excep_raised_on_host_single_client(error_host_client, error_host_client._listen_soc.excep)
        self.assert_default_state(error_host_client)

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
                         os.path.join(log_folder, "test_send_timeout_error.log"),
                         logging.DEBUG,
                         "test_send_timeout_error-filehandler")

        dummy_server.start((HOST, PORT))

        error_client.connect((HOST, PORT))
        time.sleep(0.1)
        assert error_client.send(b"Hello World!") == False

        self.assert_default_state(error_client)


    @pytest.mark.parametrize('error_client', [(TimeoutError, "sendall")], indirect=True)
    def test_send_timeout_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send_timeout_error.log"),
                         logging.DEBUG,
                         "test_send_timeout_error-filehandler")

        dummy_server.start((HOST, PORT))

        self.assert_excep_raised_on_send(error_client, error_client._soc.excep)
        assert error_client.is_connected

    @pytest.mark.parametrize('error_client', [(ConnectionError, "sendall")], indirect=True)
    def test_send_connection_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send_connection_error.log"),
                         logging.DEBUG,
                         "test_send_connection_error-filehandler")

        dummy_server.start((HOST, PORT))

        self.assert_excep_raised_on_send(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    @pytest.mark.parametrize('error_client', [(OSError, "sendall")], indirect=True)
    def test_send_os_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send_os_error.log"),
                         logging.DEBUG,
                         "test_send_os_error-filehandler")

        dummy_server.start((HOST, PORT))

        self.assert_excep_raised_on_send(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    @pytest.mark.parametrize('error_client', [(TimeoutError, "recv")], indirect=True)
    def test_recv_timeout_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_timeout_error.log"),
                         logging.DEBUG,
                         "test_recv_timeout_error-filehandler")

        dummy_server.start((HOST, PORT))

        self.assert_excep_raised_on_recv(error_client, error_client._soc.excep)
        assert error_client.is_connected

    @pytest.mark.parametrize('error_client', [(ConnectionError, "recv")], indirect=True)
    def test_recv_connection_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_connection_error.log"),
                         logging.DEBUG,
                         "test_recv_connection_error-filehandler")

        dummy_server.start((HOST, PORT))

        self.assert_excep_raised_on_recv(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    @pytest.mark.parametrize('error_client', [(OSError, "recv")], indirect=True)
    def test_recv_os_error(self, error_client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_recv_os_error.log"),
                         logging.DEBUG,
                         "test_recv_os_error-filehandler")

        dummy_server.start((HOST, PORT))

        self.assert_excep_raised_on_recv(error_client, error_client._soc.excep)
        self.assert_default_state(error_client)

    """Test send/recv functionality"""

    def test_send(self, client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send.log"),
                         logging.DEBUG,
                         "test_send-filehandler")

        msg1 = b"Hello World!"
        msg2 = b"foofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoofoo"
        with open("tests/dummy_files/doi.txt", 'rb') as file:
            text = file.read()

        dummy_server.start((HOST, PORT))
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

        dummy_server.start((HOST, PORT))
        client.connect((HOST, PORT))
        time.sleep(0.1)

        dummy_server.send(b"Hello World!")
        time.sleep(0.1)
        data = client.receive_raw(4)
        assert len(data) == 4
        assert data == b"Hell"

        dummy_server.send(b"Hello World!")
        time.sleep(0.1)
        data = client.receive_raw(12)
        assert len(data) == 12
        assert data == b"o World!Hell"

    def test_iter_receive(self, client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_iter_receive.log"),
                         logging.DEBUG,
                         "test_iter_receive-filehandler")

        msg = b"Hello World!"
        dummy_server.start((HOST, PORT))
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

        dummy_server.start((HOST, PORT))
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

        dummy_server.start((HOST, PORT))
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

        def recv_loop(server):
            try:
                server.soc.recv(1024)
            except AttributeError:
                return

        dummy_server.start((HOST, PORT))
        threading.Thread(target=recv_loop, args=[dummy_server]).start()
        with TCPClient() as client:
            client.connect((HOST, PORT))
            time.sleep(0.1)
            assert client.is_connected
            client.send(b"Hello World!")
            time.sleep(0.1)

        assert client.is_connected is False

    """Edge cases"""

    def test_connect_called_twice(self, dummy_server, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_connect_called_twice.log"),
                         logging.DEBUG,
                         "test_connect_called_twice-filehandler")

        dummy_server.start((HOST, PORT))
        client.connect((HOST, PORT))

        client.connect(("127.0.0.1", 5001))
        assert isinstance(client._soc, socket.socket)
        assert client._listen_soc is None
        assert client._local_addr is not None
        assert client._peer_addr == (HOST, PORT)
        assert client._timeout is None
        assert client._is_connected is True
        assert client._is_host is False

        client.host_single_client(("127.0.0.1", 5001), 5)
        assert isinstance(client._soc, socket.socket)
        assert client._listen_soc is None
        assert client._local_addr is not None
        assert client._peer_addr == (HOST, PORT)
        assert client._timeout is None
        assert client._is_connected is True
        assert client._is_host is False


    def test_disconnect_called_multiple_times(self, dummy_server, client, caplog):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_disconnect_called_multiple_times.log"),
                         logging.DEBUG,
                         "test_disconnect_called_multiple_times-filehandler")

        with caplog.at_level(logging.INFO):
            client.disconnect()

            dummy_server.start((HOST, PORT))
            client.connect((HOST, PORT))

            client.disconnect()
            client.disconnect()

        assert len([record for record in caplog.records if "Disconnected" in record.msg]) == 1

    def test_from_socket_not_connected(self):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_from_socket_not_connected.log"),
                         logging.DEBUG,
                         "test_from_socket_not_connected-filehandler")

        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client = TCPClient.from_socket(soc)
        assert client._soc is not None
        assert client._listen_soc is None
        assert client._peer_addr is None
        assert client._local_addr is None
        assert client._timeout is None
        assert client._is_connected is False
        assert client._is_host is False

    def test_connect_invalid_ip(self, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_connect_invalid_ip.log"),
                         logging.DEBUG,
                         "test_connect_invalid_ip-filehandler")
        with pytest.raises(ValueError):
            client.connect(("999.999.999.999", 5000))

        with pytest.raises(ValueError):
            client.connect(("127.0.0.1", 65536))

        with pytest.raises(ValueError):
            client.connect(("0.0.0.0", 5000))

        with pytest.raises(ValueError):
            client.connect(("255.255.255.255", 5000))


    def test_host_single_client_twice(self, dummy_client, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_host_single_client_twice.log"),
                         logging.DEBUG,
                         "test_host_single_client_twice-filehandler")
        threading.Thread(target=client.host_single_client, args=[(HOST, PORT), 5]).start()
        time.sleep(0.1)
        dummy_client.connect((HOST, PORT))
        time.sleep(0.1)

        remote_addr = client.peer_addr

        client.host_single_client(("127.0.0.1", 5001), timeout=0.1)

        assert client.local_addr == (HOST, PORT)
        assert client.peer_addr == remote_addr


    def test_host_single_client_invalid_ip(self, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_host_single_client_invalid_ip.log"),
                         logging.DEBUG,
                         "test_host_single_client_invalid_ip-filehandler")
        with pytest.raises(ValueError):
            client.host_single_client(("999.999.999.999", 5000), 5)

        with pytest.raises(ValueError):
            client.host_single_client(("127.0.0.1", 65536), 5)

        with pytest.raises(ValueError):
            client.host_single_client(("255.255.255.255", 5000), 5)


    def test_set_negative_timeout(self, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_set_negative_timeout.log"),
                         logging.DEBUG,
                         "test_set_negative_timeout-filehandler")
        with pytest.raises(ValueError):
            client.timeout = -1

    def test_timeout_applies_after_connect(self, dummy_server, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_timeout_applies_after_connect.log"),
                         logging.DEBUG,
                         "test_timeout_applies_after_connect-filehandler")
        client.timeout = 5
        dummy_server.start((HOST, PORT))
        client.connect((HOST, PORT))
        assert client._soc.gettimeout() == 5


    def test_receive_buffsize_zero(self, client, dummy_server):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_receive_buffsize_zero.log"),
                         logging.DEBUG,
                         "test_receive_buffsize_zero-filehandler")

        dummy_server.start((HOST, PORT))
        client.connect((HOST, PORT))

        with pytest.raises(ValueError):
            client.receive_raw(0)

        with pytest.raises(ValueError):
            client.receive(0)

        with pytest.raises(ValueError):
            for chunk in client.iter_receive(0):
                print(chunk)

    def test_send_before_connect(self, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send_before_connect.log"),
                         logging.DEBUG,
                         "test_send_before_connect-filehandler")
        with pytest.raises(ConnectionError):
            client.send(b"hello")

    def test_send_bytes_before_connect(self, client):
        add_file_handler(logger,
                         os.path.join(log_folder, "test_send_bytes_before_connect.log"),
                         logging.DEBUG,
                         "test_send_bytes_before_connect-filehandler")
        with pytest.raises(ConnectionError):
            client.send_raw(b"hello")
