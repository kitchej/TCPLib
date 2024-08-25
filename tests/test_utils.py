"""
test_client_mgmt.py
Written by: Joshua Kitchen - 2024
"""
import src.TCPLib.internals.utils as utils


class TestUtils:
    def test_encode_msg(self):
        assert utils.encode_msg(b'', 2) == bytearray(b'\x00\x00\x00\x00\x02')
        assert utils.encode_msg(b'Disconnecting', 4) == bytearray(b'\x00\x00\x00\r\x04Disconnecting')
        num = 24
        assert utils.encode_msg(num.to_bytes(4), 1) == bytearray(b'\x00\x00\x00\x04\x01\x00\x00\x00\x18')

    def test_decode_header(self):
        assert utils.decode_header(b'\x00\x00\x00\x00\x02') == (0, 2)
        assert utils.decode_header(b'\x00\x00\x00\r\x04') == (13, 4)
        assert utils.decode_header(b'\x00\x00\x00\x04\x01') == (4, 1)
