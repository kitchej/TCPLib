"""
Message.py
Written by: Joshua Kitchen - 2024
"""


class Message:
    """
    Represents a message sent over the network.
    """
    def __init__(self, size, data, client_id=None):
        self.size = size
        self.data = data
        self.client_id = client_id
