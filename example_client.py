from TCPLib import TCPClient

# with TCPClient() as client:
#     client.connect(("127.0.0.1", 5000))
#     print(f"Connected to {client.peer_addr[0]}@{client.peer_addr[1]}")
#
#     msg = bytearray(b"Hello World!")
#     client.send(msg)
#     echo = client.receive()
#     print(f"Received message from server: {echo.decode('utf-8')}")

with TCPClient() as client:
    client.connect(("127.0.0.1", 5000))
    print(f"Connected to {client.peer_addr[0]}@{client.peer_addr[1]}")
    client.send(b"requesting data")
    reply = bytearray()
    reply_generator = client.iter_receive()
    size = next(reply_generator)
    bytes_recv = 0
    for chunk in reply_generator:
        bytes_recv += len(chunk)
        reply.extend(chunk)
        print(f"Received: {bytes_recv}/{size} bytes")

    client.send(b"Msg received")

