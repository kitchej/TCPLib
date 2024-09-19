"""
utils.py
Written by: Joshua Kitchen - 2024
"""


def encode_msg(data: bytes) -> bytearray:
    """
    MSG STRUCTURE:
    [Size (4 bytes)] [Data]
    """
    msg = bytearray()
    msg.extend(len(data).to_bytes(4, byteorder='big'))
    msg.extend(data)
    return msg


def decode_header(header: bytes) -> int:
    return int.from_bytes(header, byteorder='big')
