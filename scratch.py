import time
import threading
import os
import pathlib
from datetime import datetime
import traceback
import queue

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


def client_thread(c, out: queue.Queue):
    while c.is_connected():
        reply = c.receive_all(4096)
        if not reply:
            return
        out.put(reply)



def echo(client, server, data):
    # 1.) Client sends data and waits for response from the server
    # 2.) Server receives the message and sends back how many bytes it received
    # 3.) Server waits a brief moment then echos what it received
    # 4.)
    client_messages = queue.Queue()
    client.connect(HOST, PORT)
    threading.Thread(target=client_thread, args=[client, client_messages]).start()

    server_ack = client.send(data)

    time.sleep(0.1)

    server_copy = server.pop_msg()

    server.send(server.list_clients()[0], server_copy.data)

    time.sleep(0.1)

    while not client_messages.empty():
        print(client_messages.get())

    client.disconnect()
    return



def send_text(server, client):
    with open(os.path.abspath(os.path.join("tests", "dummy_files", "DOI.txt")), 'rb') as file:
        text = file.read()

    print(echo(client, server, text))
    # time.sleep(0.1)
    #
    # assert server_reply == (4, 1, len(text))
    # assert client_reply
    #
    # assert msg["size"] == 4
    # assert msg["flags"] == 1
    # assert msg["data"] == text

    client.disconnect()


try:
    send_text(s, c)
except Exception as e:
    traceback.print_exception(e)
finally:
    s.stop()
    c.disconnect()
