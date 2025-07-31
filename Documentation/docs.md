# TCPLib Public API Documentation

## Table of Contents
- [Message](#message)
- [TCPServer](#tcpserver)
  - [Properties](#tcpserver-properties)
  - [Methods](#tcpserver-methods)
- [TCPClient](#tcpclient)
  - [Properties](#tcpclient-properties)
  - [Methods](#tcpclient-methods)
- [ClientProcessor](#clientprocessor)
  - [Properties](#clientprocessor-properties)
  - [Methods](#clientprocessor-methods)


---

## Message

### `Message(self, size, data, client_id=None)`

Represents a message sent over the network.

#### Properties
- **size:**  
  The size of the message in bytes.

- **data:**  
  Raw bytes of the message.

- **client_id:**  
  The ID of the client that sent the message.

---

## TCPServer

### `TCPServer(self, max_clients: int = 0, timeout: int = None)`

A TCP server that listens for and manages multiple TCP/IP client connections.

If `max_clients` is 0, the server allows an unlimited number of connections.
If `timeout` is None, the server socket has no timeout.

The `on_connect` parameter is a callback function that will run for every new connection. Return `False` to 
    disconnect the client. Two arguments will be passed to this function: A TCPClient object and
    the client's id

### TCPServer Properties
- **addr:**  
  A tuple representing the address the server is currently bound to. Read-only.

- **is_running:**  
  Indicates whether the server is actively listening for connections. Read-only.

- **max_clients:**  
  A positive integer indicating the maximum allowed client connections.  
  A value of 0 allows infinite connections. If setting, the new max should be a positive integer. Read-only.

- **timeout:**  
  Timeout (in seconds) for accepting new connections. A value of `None` disables timeouts.

- **client_count:**  
  The number of currently connected clients. Read-only.

- **is_full:**  
  Boolean indicating whether the server has reached `max_clients`. Read-only.

### TCPServer Methods
- **from_socket(soc: socket.socket, max_clients: int):**  
  Class method that creates a `TCPServer` from an existing bound socket.  
  Returns a new `TCPServer` instance. If bind() or listen() are called on the socket BEFORE TCPServer.start(), an exception will be raised.


- **set_client_attribute(timeout: int):**  
  Set a specific attribute of a client connection. Raises `KeyError` if the client could not be found.
        Valid attributes are:

  `"timeout"`

  `"max_timeouts"`


- **get_client_attributes(client_id: str)**
  Get information about a client given a client_id.
  Returns a dictionary with keys: 

- `"is_running"`

- `"timeout"`

- `"addr"` 

- `"total_timeouts"`

- `"max_timeouts"`


Raises KeyError if a client with client_id cannot be found


- **`list_clients()`:**  
  Return a list of client IDs for all currently connected clients.


- **`disconnect_client(client_id: str)`:**  
  Disconnects a client by ID. Raises `KeyError` if the client is not found.


- **`pop_msg(block: bool = False, timeout: int = None)`:**  
  Pops the next message from the message queue. If `block=True`, this method will block until a message is 
  available. If `block=True` and a value for `timeout` is provided, this method will block for `timeout` seconds 
  before returning. Returns `None` if the queue was empty.


- **`get_all_msg()`:**  
  A generator for iterating over the message queue. Iteration ends when the queue is empty.


- **`has_messages()`:**  
  Returns `True` if the message queue is not empty.


- **`send(client_id: str, data: bytes)`:**  
  Sends data to the client with `client_id`. Returns 'True' on successful sending, 'False' if not. Raises `KeyError` if 
  the client could not be found.


- **`start(addr: tuple[str, int])`:**  
  Starts the server and begins listening on the specified address.


- **`stop()`:**  
  Disconnects all clients and shuts down the server. If the server is not running, this method will do nothing.

---

## TCPClient

### `TCPClient(self, timeout: int = None)`

A TCP client that can connect to or host a TCP/IP connection.

### TCPClient Properties
- **is_connected:**  
  Indicates whether the client is currently connected. Read-only.

- **timeout:**  
  Timeout (in seconds) for socket operations. A value of `None` disables timeouts.

- **local_addr:**  
  Local address bound to the client socket. Returns `None` if disconnected. Read-only.

- **peer_addr:**  
  Address of the remote host. Returns `None` if disconnected. Read-only.

- **is_host:**  
  `True` if the client is acting as a server (host), otherwise `False`. Read-only.

### TCPClient Methods
- **`from_socket(soc: socket.socket, is_listen_soc=False)`:**  
  Creates a client from an existing socket object. The timeout value for the socket is overridden when
  connect() or host_single_client() is called to ensure class consistency. Returns a new TCPClient object.
  NOTE: if bind() or listen() is called on the socket before host_single_client() or connect() is called,
  both methods will raise an exception.


- **`host_single_client(addr: tuple[str, int], timeout: int = None)`:**  
  Hosts a single connection from a remote TCP/IP client. The timeout argument sets how long this
  method will listen for a connection; 'None' indicates an infinite timeout (default).
  Raises `TimeoutError`, `ConnectionError`, `OSError`, and `socket.gaierror`.


- **`connect(addr: tuple[str, int])`:**
  Connects to a remote TCP/IP host.  
  Raises `TimeoutError`, `ConnectionError`, `OSError`, or `socket.gaierror`.


- **`reconnect()`:**  
  Attempts to reconnect to the last successfully connected peer.  
  Raises ConnectionError if no prior connection exists.


- **`disconnect()`:**  
  Gracefully disconnects from the remote host. If no connection is opened, this method does nothing


- **`send_raw(data: bytes)`:**  
  Send raw bytes with no size header.


- **`send(data: bytes)`:**  
  Sends bytes with a 4-byte size header.


- **`receive_raw(size: int)`:**  
  Receives exactly `size` bytes.  
  Returns empty bytes on socket closure.  
  Raises `TimeoutError`, `ConnectionError`, or `OSError`.


- **`iter_receive(buff_size: int = 4096)`:**  
  Generator that yields chunks of a message. First yield is the total message size.


- **`receive(buff_size: int = 4096)`:**  
  Receives a full message as a `bytearray`.  
  Returns empty `bytearray` on failure or closed connection.
