"""
utils.py
Written by: Joshua Kitchen - 2024
"""

import re

IPV4_PATTERN = re.compile(r'^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$')

def vet_address(addr: tuple[str, int]):
    if len(addr) != 2:
        return False
    if not re.match(IPV4_PATTERN, addr[0]):
        return False
    if addr[1] < 0 or addr[1] > 65535:
        return False
    return True

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
