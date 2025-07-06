# TCPLib

---

**NOTE: This module was made for educational purposes and should not be considered secure.**

TCPLib is a module for setting up a simple TCP client and server. All data is sent and received as a bytes-like object (```bytes``` or ```bytearray```). 
All data received is returned as a ```bytearray```.

### Example:

server.py

    from TCPLib import TCPServer
    
    server = TCPServer()
    server.start(("127.0.0.1", 5000))
    print("Server started")
    
    client_msg = server.pop_msg(block=True)
    print(f"Message received: {client_msg.data.decode('utf-8')}")
    server.send(client_msg.client_id, client_msg.data)
    
    server.stop()
    print("Server stopped")

client.py

    from TCPLib import TCPClient
    
    client = TCPClient()
    client.connect(("127.0.0.1", 5000))
    print(f"Connected to {client.host_addr[0]}@{client.host_addr[1]}")
    
    client.send(b"Hello World!")
    echo = client.receive()
    print(f"Received message from server: {echo.decode('utf-8')}")
    
    client.disconnect()

Output server.py

    Server started
    Message received: Hello World!
    Server stopped

    Process finished with exit code 0

Output client.py

    Connected to 127.0.0.1@5000
    Received message from server: Hello World!
    
    Process finished with exit code 0


It is also possible for a TCPClient object to host a single TCP/IP connection. Below is an example where client.py
connects to a host client instead of a server:

host_client.py 

    from TCPLib import TCPClient
    
    client = TCPClient()
    print(f"Listening for a connection...")
    client.host_single_client(("127.0.0.1", 5000))
    
    client_msg = client.receive()
    print(f"Message received from {client.remote_addr[0]}@{client.remote_addr[1]}: {client_msg.decode('utf-8')}")
    client.send(client_msg)
    
    client.disconnect()

output:

    Listening for a connection...
    Message received from 127.0.0.1@57003: Hello World!
    Process finished with exit code 0


### Installation


**Requires Python 3.10 or higher**

Install with pip:

```pip install TCPLib```
