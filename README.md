# TCPLib

---

**NOTE: This library was made for educational purposes and should not be considered secure.**

TCPLib is a library for setting up a simple TCP client and server. All data is sent and received as a bytes-like object (```bytes``` or ```bytearray```). 
All data received is returned as a ```bytearray```.

### Example:

server.py

    from TCPLib.tcp_server import TCPServer
    import time

    server = TCPServer("127.0.0.1", 5000)
    server.start()
    print("Server started")

    client_msg = server.pop_msg(block=True)
    print(f"Message received: {client_msg.data.decode('utf-8')}")
    server.send(client_msg.client_id, client_msg.data)

    time.sleep(0.1)
    server.stop()
    print("Server stopped")

client.py

    from TCPLib.tcp_client import TCPClient
    
    client = TCPClient("127.0.0.1", 5000)
    client.connect()
    print(f"Connected to {client.addr[0]}@{client.addr[1]}")
    
    client.send(b"Hello World!")
    echo = client.receive_all()
    print(f"Received message from server: {echo.data.decode('utf-8')}")
    
    client.disconnect()

Output client.py

    Connected to 127.0.0.1@5000
    Received message from server: Hello World!
    
    Process finished with exit code 0

Output server.py

    Server started
    Message received: Hello World!
    Server stopped
    
    Process finished with exit code 0



### Installation

This package is not available on pypi at the moment, but can still be installed with pip:

1.) Download the wheel file ```TCP_Lib-3.0.0-py3-none-any.whl``` from the releases page

2.) In the terminal execute: ```pip install [path to wheel file]```
