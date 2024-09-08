"""
Message.py
Written by: Joshua Kitchen - 2024
"""


class Message:
    """
    A class for holding information about messages received.
    """
    def __init__(self, client_id, size, flags, data):
        self.client_id = client_id
        self.size = size
        self.flags = flags
        self.data = data

    def __str__(self):
        return f"{self.__repr__()} client_id={self.client_id}, size={self.size}, flags={self.flags}"
