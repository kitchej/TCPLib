"""
utils.py
Written by: Joshua Kitchen - 2024
"""


def encode_msg(data: bytes, flags: int):
    """
    MSG STRUCTURE:
    [Header: 5 bytes] [Data: inf bytes]

    HEADER STRUCTURE:
    [Size: 4 bytes] [Flags: 1 Byte -> 1 ----
                                      1     |
                                      1     | --- CURRENTLY UNUSED
                                      1     |
                                      1 ____
                                      1: DISCONNECTING
                                      1: TRANSMITTING DATA
                                      1: REPORTING BYTES RECEIVED]
    """
    msg = bytearray()
    size = len(data).to_bytes(4, byteorder='big')
    flags = flags.to_bytes(1, byteorder='big')
    msg.extend(size)
    msg.extend(flags)
    msg.extend(data)
    return msg


def decode_header(header: bytes):
    size = int.from_bytes(header[0:4], byteorder='big')
    flags = int.from_bytes(header[4:5], byteorder='big')
    return size, flags
