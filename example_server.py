from TCPLib import TCPServer

server = TCPServer()
server.start(("127.0.0.1", 5000))
print("Server started")

client_msg = server.pop_msg(block=True)
print(f"Message received: {client_msg.data.decode('utf-8')}")
server.send(client_msg.client_id, client_msg.data)

server.stop()
print("Server stopped")
