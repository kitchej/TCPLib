

- [TCPLib Documentation](#tcplib-documentation)
  - [**Message(self, size, data, client\_id=None)**](#messageself-size-data-client_idnone)
    - [**Properties**](#properties)
  - [**TCPServer(self, max\_clients: int = 0, timeout: int = None)**](#tcpserverself-max_clients-int--0-timeout-int--none)
    - [**Properties**](#properties-1)
    - [**Methods**](#methods)
  - [**TCPClient(self, timeout: int = None)**](#tcpclientself-timeout-int--none)
    - [**Properties**](#properties-2)
    - [**Methods**](#methods-1)

---
# TCPLib Documentation


## **Message(self, size, data, client_id=None)**

### **Properties**
* **size:** 
Size of the message in bytes

* **data:**
Raw bytes of the message

* **client_id:** 
Id of the client who sent the message

---
## **TCPServer(self, max_clients: int = 0, timeout: int = None)**

A TCP Server that can listen for and manage multiple TCP/IP client connections. If max_clients is 0, then the server capacity will
be infinite. If timeout is None, the timeout will be infinite.

### **Properties**

* **addr:** 
A tuple with the current address the server is listening on. Read only.


* **is_running:** 
A boolean indicating whether the server is set up and running. Read only.


* **max_clients:** 
An positive integer representing the maximum allowed connections. Zero indicates that the server will allow infinite
connections.


* **timeout:** 
A positive integer representing the amount of time the server will wait on a connection. A value of None indicates an infinite timeout.


* **client_count:** 
An int representing the number of connected clients. Read only.


* **is_full:** 
A boolean indicating if the server is full. Read only.


* **client_count:** 
An int representing the number of connected clients. Read only.

### **Methods**

* **set_clients_timeout(timeout: ```int```):** 

    Sets the timeout (in seconds) of the all current client sockets. The Timeout argument should be a positive integer. Passing None will set the timeout to infinity. Returns True on success, False if not. ee https://docs.python.org/3/library/socket.html#socket-timeouts for more information about timeouts.


* **list_clients():** 

    Returns a list with the client ids of all connected clients.


* **get_client_info(client_id: ```str```)** 

    Gives basic info about a client given a client_id. Returns a dictionary with keys 'is_running', 'timeout', 'addr'. Returns None if a client with client_id cannot be found.


* **disconnect_client(client_id: ```str```)** 

    Disconnects a client with client_id. Returns False if no client with client_id was connected, True on a successful disconnect.


* **pop_msg(self, block: ```bool``` = False, timeout: ```int``` = None)**

    Get the next message in the queue. If block is True, this method will block until it can pop a message from the queue, otherwise it will try to get a value and return None if queue is empty. If block is True and a timeout is given, block until timeout expires and then return None if no item was received.
    See  https://docs.python.org/3/library/queue.html#queue.Queue.get for more information.


* **get_all_msg(self, block: ```bool``` = False, timeout: ```int``` = None)**

    Generator for iterating over the message queue. If block is True, each iteration of this method will block until it
    can pop something from the queue, else it will try to get a value and yield None if queue is empty. If block
    is True and a timeout is given, block until timeout expires and then yield None if no item was received.
    See  https://docs.python.org/3/library/queue.html#queue.Queue.get for more information.


* **has_messages()**

    Returns a boolean indicating if the message queue has any messages.


* **send(client_id: ```str```, data: ```bytes```)**

    Sends data to a connected client. Returns True on successful sending, False if not or if a client with
    client_id could not be found.


* **start(addr: ```tuple[str, int]```)**

    Starts the server and listens for connections on the address provided. Returns True on successful start up, False if not.


* **stop(addr: ```tuple[str, int]```)**

    Stops the server. If the server is not running, this method will do nothing.

---
## **TCPClient(self, timeout: int = None)**

A TCP client that can connect to a TCP/IP host

### **Properties**


* **is_connected:** 
A boolean indicating if the client is connected. Read only.


* **timeout:** 
A positive integer representing the amount of time the client will wait on a connection. A value of None indicates an infinite timeout.

  
* **host_addr:** 
Returns a tuple with the host connection's address. Read only.


* **remote_addr:** 
Returns a tuple with the remote connection's address. Read only.

* **is_host:** 
Returns a boolean indicating if this client is the host. Read only.


### **Methods**


* **host_single_client(addr: ```tuple[str, int]```, timeout: ```int``` = None)**

    Hosts a single connection from another TCP/IP client. The timeout argument sets how long this
    method will listen for a connection. Raises TimeoutError, ConnectionError, and socket.gaierror.


* **connect(addr: ```tuple[str, int]```)**

    Initiates a connection to a TCP/IP host. Raises TimeoutError, ConnectionError, and socket.gaierror.


* **disconnect()**

    Disconnect from the currently connected host. If no connection is opened, this method does nothing.


* **send(data: ```bytes```)**

    Send raw bytes. Attaches a 4 bytes size header before sending. Raises TimeoutError, ConnectionError, and OSError.


* **iter_receive(buff_size: ```int``` = 4096)**

    Returns a generator for iterating over the bytes of an incoming message. An integer representing the message
    size is yielded first. Subsequent calls yield the contents of the message as it is received. Raises
    TimeoutError, ConnectionError, and OSError.

* **receive()**

    Receive raw bytes. Returns a bytearray. Raises TimeoutError, ConnectionError, and OSError.
