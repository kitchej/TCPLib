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

The `on_connect` parameter is a callback function that will run for every new connection. Return 'False' to 
    disconnect the client. Two arguments will be passed to this function: A TCPClient object and
    the client's id

### TCPServer Properties
- **addr:**  
  A tuple representing the address the server is currently bound to. Read-only.

- **is_running:**  
  Indicates whether the server is actively listening for connections. Read-only.

- **max_clients:**  
  A positive integer indicating the maximum allowed client connections.  
  A value of 0 means unlimited.

- **timeout:**  
  Timeout (in seconds) for accepting new connections. A value of `None` disables timeouts.

- **client_count:**  
  The number of currently connected clients. Read-only.

- **is_full:**  
  Boolean indicating whether the server has reached `max_clients`. Read-only.

### TCPServer Methods
- **from_socket(soc: socket.socket, max_clients: int):**  
  Class method that creates a `TCPServer` from an existing bound socket.  
  Returns a new `TCPServer` instance. Example:


     server = TCPServer.from_socket(soc, max_clients=25)


- **set_client_attribute(timeout: int):**  
  Set a specific attribute of a client connection. Raises KeyError if the client could not be found
        Valid attributes are:

  `"timeout"`

  `"max_timeouts"`


- **get_client_attributes(client_id: str)**
  Get information about a client given a client_id.
  Returns a dictionary with keys `"is_running"`, `"timeout"`, `"addr"`, `"total_timeouts"`, and `"max_timeouts"`.
  Raises KeyError if a client with client_id cannot be found


- **list_clients():**  
  Return a list of client IDs for all currently connected clients.


- **get_client_info(client_id: str):**  
  Get a dictionary with keys `is_running`, `timeout`, and `addr` for the specified client.  
  Returns `None` if the client cannot be found.


- **get_client_attributes(client_id: str):**  
  Returns a dictionary with keys `is_running`, `timeout`, `addr`, `total_timeouts`, and `max_timeouts`.  
  Raises `KeyError` if the client cannot be found.


- **set_client_attribute(client_id: str, attribute: str, value):**  
  Sets a specific attribute (`timeout` or `max_timeouts`) for a given client.  
  Raises `KeyError` or `ValueError` if the attribute is invalid or the client doesn't exist.


- **disconnect_client(client_id: str):**  
  Disconnect a client by ID. Raises `KeyError` if the client is not found.


- **pop_msg(block: bool = False, timeout: int = None):**  
  Pops the next message from the queue. If `block=True`, this method will block until a message is 
  available. If `block=True` and a value for `timeout` is provided, this method will block for `timeout` seconds 
  before returning. Returns None if the queue was empty.


- **get_all_msg(block: bool = False, timeout: int = None):**  
  A generator for iterating over the message queue. Iteration ends when the queue is empty.


- **has_messages():**  
  Returns `True` if the message queue is not empty.


- **send(client_id: str, data: bytes):**  
  Send data to the client with `client_id`. Returns 'True' on successful sending, 'False' if not. Raises `KeyError` if 
  the client could not be found.


- **start(addr: tuple[str, int]):**  
  Starts the server and begins listening on the specified address.


- **stop():**  
  Stops the server and disconnects all clients.

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
  Local address bound to the client socket. Returns `None` if disconnected.

- **peer_addr:**  
  Address of the remote host. Returns `None` if disconnected.

- **is_host:**  
  `True` if the client is acting as a server (host), otherwise `False`.

### TCPClient Methods
- **from_socket(soc: socket.socket, is_listen_soc=False):**  
  Creates a TCPClient instance from a raw socket.  
  `is_listen_soc=True` marks it as a listening host socket.

- **host_single_client(addr: tuple[str, int], timeout: int = None):**  
  Hosts a connection from a remote client.  
  Waits for one connection, raising on timeout or connection failure.

- **connect(addr: tuple[str, int]):**  
  Connects to a remote TCP/IP server.  
  Raises `TimeoutError`, `ConnectionError`, `OSError`, or `socket.gaierror`.

- **reconnect():**  
  Attempts to reconnect to the last successfully connected peer.  
  Raises if no prior connection exists.

- **disconnect():**  
  Gracefully disconnects from the remote host.

- **send_bytes(data: bytes):**  
  Sends raw bytes with no header.  
  Raises on timeout or connection failure.

- **send(data: bytes):**  
  Sends bytes with a 4-byte size header.

- **receive_bytes(size: int):**  
  Receives exactly `size` bytes.  
  Returns empty bytes on socket closure.  
  Raises `TimeoutError`, `ConnectionError`, or `OSError`.

- **iter_receive(buff_size: int = 4096):**  
  Generator that yields chunks of a message. First yield is the total message size.

- **receive(buff_size: int = 4096):**  
  Receives a full message as a `bytearray`.  
  Returns empty `bytearray` on failure or closed connection.

---

## ClientProcessor

### `ClientProcessor(client_id, client_soc, msg_q, ...)`

Maintains a dedicated connection to a single client. Runs a background thread to receive messages and places them in a shared queue.

### ClientProcessor Properties
- **id:**  
  The ID string identifying this client processor.

- **timeout:**  
  Timeout value used for receiving data. Can be modified at runtime.

- **total_timeouts:**  
  The number of times this client has timed out while waiting for messages.

- **max_timeouts:**  
  The max allowed timeouts before the client is forcibly disconnected.

- **remote_addr:**  
  A `(host, port)` tuple identifying the remote client.

- **is_running:**  
  Indicates whether the client processor thread is running.

### ClientProcessor Methods
- **start():**  
  Begins the client processor's background thread. Does nothing if already running.

- **stop(suppress_callback=False):**  
  Stops the background thread and disconnects the client.  
  If `suppress_callback=True`, the `on_disconnect` hook will not be invoked.

- **send(data: bytes):**  
  Sends a message to the connected client with a 4-byte header.  
  Returns `True` on success, `False` if the processor is not active.
