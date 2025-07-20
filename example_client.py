import TCPLib
import socket
HOST = "127.0.0.1"
PORT = 5000

# with TCPClient() as client:
#     client.connect(("127.0.0.1", 5000))
#     print(f"Connected to {client.peer_addr[0]}@{client.peer_addr[1]}")
#
#     client.send(b"Hello World!")
#     echo = client.receive()
#     print(f"Received message from server: {echo.decode('utf-8')}")

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
soc.bind((HOST, PORT))
client = TCPLib.TCPClient.from_socket(soc)

client.connect((HOST, PORT))


