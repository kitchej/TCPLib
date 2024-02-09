class Message:
    def __init__(self, client_id, size, flags, data):
        self.client_id = client_id
        self.size = size
        self.flags = flags
        self.data = data
