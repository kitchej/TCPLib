from TCPLib import TCPClient

with TCPClient() as client:
    client.connect(("127.0.0.1", 5000))
    print(f"Connected to {client.peer_addr[0]}@{client.peer_addr[1]}")

    client.send(b"Hello World!")
    echo = client.receive()
    print(f"Received message from server: {echo.decode('utf-8')}")


