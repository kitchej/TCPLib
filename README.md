# TCPLib

---

> **⚠️ This module was created for educational purposes and should not be considered secure.**

TCPLib is a Python module for setting up simple TCP clients and servers. All data is sent as a bytes-like object (`bytes` or `bytearray`).  
Data received by a `TCPClient` object is returned as a `bytearray`. Data received by a `TCPServer` object is returned as a `Message` object.

---

### Example

#### `server.py`

```python
from TCPLib import TCPServer

server = TCPServer()
server.start(("127.0.0.1", 5000))
print("Server started")

client_msg = server.pop_msg(block=True)
print(f"Message received: {client_msg.data.decode('utf-8')}")
server.send(client_msg.client_id, client_msg.data)

server.stop()
print("Server stopped")
```

#### `client.py`

```python
from TCPLib import TCPClient

with TCPClient() as client:
    client.connect(("127.0.0.1", 5000))
    print(f"Connected to {client.peer_addr[0]}@{client.peer_addr[1]}")

    client.send(b"Hello World!")
    echo = client.receive()
    print(f"Received message from server: {echo.decode('utf-8')}")
```

#### Output (`server.py`)

```
Server started
Message received: Hello World!
Server stopped
```

#### Output (`client.py`)

```
Connected to 127.0.0.1@5000
Received message from server: Hello World!
```

---

It is also possible for a `TCPClient` object to host a single TCP connection.  
Below is an example where `client.py` connects to a host client instead of a server:

#### `host_client.py`

```python
from TCPLib import TCPClient

client = TCPClient()
print("Listening for a connection...")
client.host_single_client(("127.0.0.1", 5000))

client_msg = client.receive()
print(f"Message received from {client.peer_addr[0]}@{client.peer_addr[1]}: {client_msg.decode('utf-8')}")
client.send(client_msg)

client.disconnect()
```

#### Output

```
Listening for a connection...
Message received from 127.0.0.1@50308: Hello World!
```

---

### Installation

**Requires Python 3.10 or higher**

Install via pip:

`pip install TCPLib`

---

### Bug fixes for 2.0.1
#### TCPServer
- When a client disconnects, an empty message is now put in the message queue. This makes it easier for applications 
to know when a client connection has been closed. I had originally included this behavior in an older development version, and it's
a mystery why it was removed.
- Fixed a bug where logging errors were being caught and handled like module errors. I went ahead and evaluated *all* try/except
blocks and moved excess code out them.
- Revised some of the logging.

### What's New in Version 2.x

#### General

- Added improved and more consistent logging throughout the module.
- Enhanced exception handling with clearer, more descriptive error messages.
- Removed empty setters from all classes. Attempting to set a read-only property now raises `AttributeError`.
- Address values are now validated, and invalid addresses will raise `ValueError`.

#### TCPServer

- Updated client ID generation to a simpler, more reliable method with better uniqueness.
- Instead of `on_connect` being an overridable method, it is now a callback function passed to `TCPSerer.__init__()`. This saves the end user from having to subclass TCPServer just to use this functionality.
- The server now tracks timeouts for each client. You can configure both `timeout` and `max_timeouts` per client using `set_client_attributes()` (formerly `set_clients_timeout()`).
- The `get_all_msg()` method no longer accepts `block` or `timeout` parameters. Its purpose is to retrieve already-queued messages, so blocking is unnecessary in hindsight.

#### TCPClient

- Now supports usage with a context manager, automatically calling `disconnect()` on exit.
- Renamed `host_addr()` and `remote_addr()` to `local_addr()` and `peer_addr()` for clarity. The former naming caused confusion as the role of the client changed dynamically, requiring the user to know the classes role or call `is_host()` to find out. Now:
  - `local_addr()` always returns the address assigned to the class.
  - `peer_addr()` always returns the address of the connected remote peer.
- Renamed `send_bytes()` and `receive_bytes()` to `send_raw()` and `receive_raw()`, respectively. The old names were misleading as all data in this library is sent as bytes. The new names for these methods better reflect their intended purpose.
