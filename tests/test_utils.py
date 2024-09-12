"""
test_client_mgmt.py
Written by: Joshua Kitchen - 2024
"""
import src.TCPLib.utils as utils


class TestUtils:
    def test_encode_msg(self):
        assert utils.encode_msg(b'') == bytearray(b'\x00\x00\x00\x00')
        assert utils.encode_msg(b'Disconnecting') == bytearray(b'\x00\x00\x00\rDisconnecting')
        num = 24
        assert utils.encode_msg(num.to_bytes(4)) == bytearray(b'\x00\x00\x00\x04\x00\x00\x00\x18')

    def test_decode_header(self):
        assert utils.decode_header(b'\x00\x00\x00\x00') == 0
        assert utils.decode_header(b'\x00\x00\x00\r') == 13
        assert utils.decode_header(b'\x00\x00\x00\x04') == 4
