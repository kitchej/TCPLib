"""
Message.py
Written by: Joshua Kitchen - 2024
"""


class Message:
    """
    Container class for holding the size and data of a message

    A message with size=0 and data=None indicates the connection has been closed
    """
    def __init__(self, size, data, client_id=None):
        self.size = size
        self.data = data
        self.client_id = client_id
