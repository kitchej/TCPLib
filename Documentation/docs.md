from src.TCPLib.tcp_client import TCPClient

# TCPLib Public API Documentation

## Table of Contents
- [Message](#message)
- [TCPServer](#tcpserver)  
  - [Properties](#tcpserver-properties)  
  - [Methods](#tcpserver-methods)
- [TCPClient](#tcpclient)  
  - [Properties](#tcpclient-properties)  
  - [Methods](#tcpclient-methods)

---

## Message

### `Message(self, size, data, client_id=None)`

Represents a message sent over the network.

#### Properties
- `size`  
  The size of the message in bytes.


- `data`  
  Raw bytes of the message.


- `client_id`  
  The ID of the client that sent the message.

---

## TCPServer

### `TCPServer(max_clients: int = 0, timeout: int | float | None = None, on_connect: Callable[[TCPClient, str], bool] | None = None):`

A TCP server that listens for and manages multiple TCP/IP client connections.

- If `max_clients` is `0`, the server allows an unlimited number of connections.  
- If `timeout` is `None`, the server socket has no timeout.  
- The `on_connect` parameter is a callback that runs for every new connection. Return `False` to disconnect the client.  
  Two arguments are passed to this function: a `TCPClient` object and the client's ID.

### TCPServer Properties

- `addr`  
  A tuple representing the address the server is currently bound to. *(Read-only)*


- `is_running`  
  Indicates whether the server is actively listening for connections. *(Read-only)*


- `max_clients`  
  A positive integer indicating the maximum allowed client connections. A value of `0` allows infinite connections. *(Read-only)*


- `timeout`  
  Timeout (in seconds) for accepting new connections. A value of `None` disables timeouts.


- `client_count`  
  The number of currently connected clients. *(Read-only)*


- `is_full`  
  Boolean indicating whether the server has reached `max_clients`. *(Read-only)*

### TCPServer Methods

- `from_socket(soc: socket.socket, max_clients: int)`  
  Class method that creates a `TCPServer` object from an existing socket.  
  Returns a new `TCPServer` instance.  
  > ⚠️ If `bind()` or `listen()` are called on the socket **before** `TCPServer.start()`, an exception will be raised.


- `set_client_attribute(timeout: int)`  
  Sets a specific attribute of a client connection. Raises `KeyError` if the client is not found.  
  Valid attributes:
  - `timeout`
  - `max_timeouts`


- `get_client_attributes(client_id: str)`  
  Returns a dictionary of information about the client with the given `client_id`. Raises `KeyError` if the client is not found.  
  Keys include:
  - `is_running`
  - `timeout`
  - `addr`
  - `total_timeouts`
  - `max_timeouts`


- `list_clients()`  
  Returns a list of client IDs for all currently connected clients.


- `disconnect_client(client_id: str)`  
  Disconnects a client by ID. Raises `KeyError` if the client is not found.


- `pop_msg(block: bool = False, timeout: int = None)`  
  Pops the next message from the message queue.  
  - If `block=True`, the method blocks until a message is available.  
  - If `block=True` and `timeout` is set, the method blocks for `timeout` seconds before returning.  
  Returns `None` if the queue is empty.


- `get_all_msg()`  
  Generator for iterating over all messages in the queue. Iteration ends when the queue is empty.


- `has_messages()`  
  Returns `True` if the message queue is not empty.


- `send(client_id: str, data: bytes)`  
  Sends data to the client with the specified `client_id`. Returns `True` on success, `False` on failure. Raises `KeyError` if the client is not found.


- `start(addr: tuple[str, int])`  
Starts the server and begins listening on the specified address.


- `stop()`  
  Disconnects all clients and shuts down the server. If the server is not running, this method does nothing.

---

## TCPClient

### `TCPClient(self, timeout: int | float | None = None, is_component=False)`

A TCP client that can connect to or host a TCP/IP connection.

The `is_component` argument indicates that TCPClient is a member of another class, specifically a ClientProcessor. This will supress log
messages in _handle_error(), receive_bytes(), send_bytes(), and disconnect(), since ClientProcessor
already has its own logging for these functions.

### TCPClient Properties

- `is_connected`  
  Indicates whether the client is currently connected. *(Read-only)*


- `timeout`  
  Timeout (in seconds) for network operations. A value of `None` disables timeouts.


- `local_addr`  
  Local address bound to the client socket. Returns `None` if disconnected. *(Read-only)*


- `peer_addr`  
  Address of the remote host. Returns `None` if disconnected. *(Read-only)*


- `is_host`  
  `True` if the client is acting as a server (host), otherwise `False`. *(Read-only)*

### TCPClient Methods

- `from_socket(soc: socket.socket, is_listen_soc=False)`  
  Creates a client from an existing socket. Overrides the socket timeout when `connect()` or `host_single_client()` is called. Returns a new `TCPClient` object.  
  > ⚠️ If `bind()` or `listen()` is called on the socket before calling `host_single_client()` or `connect()`, both methods will raise an exception.


- `host_single_client(addr: tuple[str, int], timeout: int = None)`  
  Hosts a single connection from a remote TCP/IP client. The `timeout` argument defines how long to listen; `None` means wait indefinitely.


- `connect(addr: tuple[str, int])`  
  Connects to a remote TCP/IP host.


- `reconnect()`  
  Attempts to reconnect to the last successfully connected peer. Raises `ConnectionError` if no previous connection exists.


- `disconnect()`  
  Gracefully disconnects from the remote host. If not connected, this method does nothing.


- `send_raw(data: bytes)`  
  Sends raw bytes with **no size header**.


- `send(data: bytes)`  
  Sends bytes with a 4-byte size header.


- `receive_raw(size: int)`  
  Receives exactly `size` bytes. Returns an empty bytes object if the socket is closed.


- `iter_receive(buff_size: int = 4096)`  
  Generator that yields chunks of a message. Expects a 4-byte size header. The first yield will always be the total message size.
  Useful for keeping track of progress when receiving large messages.

  Example:
  

```python
from TCPLib import TCPClient
client = TCPClient()
# ...
reply = bytearray()
reply_generator = client.iter_receive()
size = next(reply_generator)
bytes_recv = 0
for chunk in reply_generator:
    bytes_recv += len(chunk)
    reply.extend(chunk)
    print(f"Received: {bytes_recv}/{size} bytes")
```

- `receive(buff_size: int = 4096)`  
  Receives a full message as a `bytearray`. Returns an empty `bytearray` on failure or closed connection. Expects a 4-byte size header.

---