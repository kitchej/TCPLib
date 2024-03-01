import time
import threading
import os
import pathlib
from datetime import datetime

import TCPLib.TCPClient as TCPClient
import TCPLib.TCPServer as TCPServer


def thread_log(thread_id, label, msg):
    print(f"{datetime.strftime(datetime.now(), '%I:%M:%S %p')} - {thread_id}: \n\t{label} = {msg}")


HOST = "127.0.0.1"
PORT = 5000

s = TCPServer.TCPServer(
    HOST,
    PORT,
    logging_level=TCPServer.DEBUG,
    log_path=os.path.join(pathlib.Path.home(), ".server_log")
)
s.start()
time.sleep(0.1)
c = TCPClient.TCPClient(
        HOST,
        PORT,
        logging_level=TCPClient.DEBUG,
        log_path=os.path.join(pathlib.Path.home(), ".server_log")
    )


def recv(c, out: dict):
    reply = c.receive_all(4096)

    if not reply:
        raise AssertionError
    reply = c.receive_all(4096)
    thread_log("recv", "reply", reply)
    out.update({"size": reply[0]})
    out.update({"flags": reply[1]})
    out.update({"data": reply[2]})


def echo(client, server, data):
    """
    1.) Client sends message to server
    2.) Server sends message to client
    """
    time.sleep(0.1)
    client.connect(HOST, PORT)
    server_reply = client.send(data)

    thread_log("main", "server_reply", server_reply)

    time.sleep(0.1)
    msg = server.pop_msg()

    thread_log("main", 'msg', msg.data)

    echo_msg = {}
    recv_th = threading.Thread(target=recv, args=[client, echo_msg])
    recv_th.start()

    time.sleep(0.1)

    client_reply = server.send(msg.client_id, msg.data)

    # thread_log("main", 'client_reply', client_reply)

    return server_reply, client_reply, echo_msg


def send_text(server, client):
    with open(os.path.abspath(os.path.join("tests", "dummy_files", "DOI.txt")), 'rb') as file:
        text = file.read()

    server_reply, client_reply, msg = echo(client, server, text)
    time.sleep(0.1)

    # thread_log("main", "server_reply", server_reply)
    # thread_log("main", 'client_reply', client_reply)
    # thread_log("main", 'msg', msg)

    assert server_reply == (4, 1, len(text))
    assert client_reply

    assert msg["size"] == 4
    assert msg["flags"] == 1
    assert msg["data"] == text

    client.disconnect()


try:
    send_text(s, c)
except Exception as e:
    print(e)
finally:
    s.stop()
    c.disconnect()