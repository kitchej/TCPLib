"""
test_client_mgmt.py
Written by: Joshua Kitchen - 2024
"""
import TCPLib.utils as utils


class TestUtils:
    def test_encode_msg(self):
        assert utils.encode_msg(b'Disconnecting') == bytearray(b'\x00\x00\x00\rDisconnecting')
        num = 24
        assert utils.encode_msg(num.to_bytes(4, byteorder='big')) == bytearray(b'\x00\x00\x00\x04\x00\x00\x00\x18')
        num = 9999
        assert utils.encode_msg(num.to_bytes(4, signed=True, byteorder='big')) == bytearray(b"\x00\x00\x00\x04\x00\x00\x27\x0f")
        num = 4539875
        assert utils.encode_msg(num.to_bytes(6, signed=True, byteorder='big')) == bytearray(b'\x00\x00\x00\x06\x00\x00\x00EE\xe3')
        num = -1
        assert utils.encode_msg(num.to_bytes(4, signed=True, byteorder='big')) == bytearray(b'\x00\x00\x00\x04\xff\xff\xff\xff')
        num = -9999
        assert utils.encode_msg(num.to_bytes(4, signed=True, byteorder='big')) == bytearray(b'\x00\x00\x00\x04\xff\xff\xd8\xf1')
        num = -4539875
        assert utils.encode_msg(num.to_bytes(4, signed=True, byteorder='big')) == bytearray(b'\x00\x00\x00\x04\xff\xba\xba\x1d')

    def test_decode_header(self):
        assert utils.decode_header(b'\x00\x00\x00\x00') == 0
        assert utils.decode_header(b'\x00\x00\x00\r') == 13
        assert utils.decode_header(b'\x00\x00\x00\x04') == 4
        assert utils.decode_header(b'\x00\x00\x87\x76') == 34678
        assert utils.decode_header(b'\x02\xB3\xEB\x83') == 45345667
