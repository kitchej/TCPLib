import time

from TCPLib import TCPServer

# server = TCPServer()
# server.start(("127.0.0.1", 5000))
# print("Server started")
#
# client_msg = server.pop_msg(block=True)
# print(f"Message received: {client_msg.data.decode('utf-8')}")
# server.send(client_msg.client_id, client_msg.data)
#
# server.stop()
# print("Server stopped")

server = TCPServer()
server.start(("127.0.0.1", 5000))
print("Server started")

client_msg = server.pop_msg(block=True)
print(f"Message received: {client_msg.data.decode('utf-8')}")
with open("tests/dummy_files/video1.mkv", 'rb') as file:
    server.send(client_msg.client_id, file.read())


awk = server.pop_msg(block=True, timeout=5)

print(awk.data)
server.stop()
print("Server stopped")

