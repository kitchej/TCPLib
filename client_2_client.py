from TCPLib import TCPClient

client = TCPClient()
print(f"Listening for a connection...")
client.host_single_client(("127.0.0.1", 5000))

client_msg = client.receive()
print(f"Message received from {client.peer_addr[0]}@{client.peer_addr[1]}: {client_msg.decode('utf-8')}")
client.send(client_msg)

client.disconnect()
