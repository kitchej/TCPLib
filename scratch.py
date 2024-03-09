import time
import traceback
import queue

from src.TCPLib.tcp_server import TCPServer
from src.TCPLib.active_client import ActiveTcpClient


HOST = "127.0.0.1"
PORT = 5000

s = TCPServer(
    HOST,
    PORT
)
s.start()
time.sleep(0.1)
msg_queue = queue.Queue()
c = ActiveTcpClient(
    HOST,
    PORT,
    msg_queue)
c.start()


def echo(client, server, data, client_msg_q):
    time.sleep(0.1)
    client_id = server.list_clients()[0]
    client.send(data)

    server_copy = server.pop_msg(block=True)
    client_reply = server.pop_msg(block=True)
    server.send(client_id, server_copy.data)

    client_copy = client_msg_q.get(block=True)
    server_reply = client_msg_q.get(block=True)

    print("CLIENT: ", client_reply.size, client_reply.flags, client_reply.data)
    print("SERVER: ", server_reply.size, server_reply.flags, server_reply.data)

    server_copy = {
        "size": server_copy.size,
        "flags": server_copy.flags,
        "data": server_copy.data
        }
    client_copy = {
        "size": client_copy.size,
        "flags": client_copy.flags,
        "data": client_copy.data
    }

    return server_copy, client_copy


try:
    server_msg, client_msg = echo(c, s, b"Hello World", msg_queue)
    print(server_msg)
    print(client_msg)
except Exception as e:
    traceback.print_exception(e)
finally:
    s.stop()
    c.stop()
