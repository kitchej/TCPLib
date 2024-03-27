# TCPLib

---

**NOTE: This library should not be considered a secure way to transmit data. Data is transmitted as-is, so any senstive data should be secured before being sent over public networks. Use at your own risk!**

TCPLib is a library for setting up a simple TCP clinet and server. All data is sent as bytes, therefore data must be converted to a ```bytes()``` or ```bytearray()``` object before sending.

The server is equipped to handle multiple client connections and provides an interface for managing those connections. Messages sent to the server are placed in a queue which can be accessed with the class interface.

On the client side, two options are provided:

The ActiveTcPClient, once started, will always be listening for messages from the server. Messages can be sent and replies will automatically be received and placed in a queue. The class provides an interface for accessing this queue.

The PassiveTcPClient class is more flexible and gives the application devloper more control over when and how messsages are sent and received. Due to this flexibility, messages queueing is left to the application devloper.





