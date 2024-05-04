# TCPLib Documentation

---

### class TCPServer(host, port, max_clients=0, timeout=None)

Creates a TCP Server that will listen for connections on the address supplied by host and port. The max_clients argument takes a positive integer.
If max_clients is zero, then the server will accept an infinite number of client connections. The timeout argument is a positive integer representing the time in seconds the server should wait on a connection.

#### start_client_proc(client_id, host, port, cli
