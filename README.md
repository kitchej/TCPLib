# TCPLib

---

**NOTE: This library was made for educational purposes and should not be considered secure.**

TCPLib is a library for setting up a simple TCP clinet and server. All data is sent as bytes, so all data must be converted to a ```bytes()```object before sending. All data received is returned as a ```bytearray()```.

TCPServer is equipped to handle multiple client connections and provides an interface for managing those connections. Messages sent to the server are placed in a queue which can be accessed with the class interface.

ActiveTCPClient, once started, will always be listening for messages from the server.

The PassiveTCPClient class is more flexible and gives the application devloper more control over when and how messsages are sent and received.





