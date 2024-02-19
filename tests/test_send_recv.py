import time
import threading
import os

from tests.fixtures import dummy_client, dummy_server, server, client, HOST, PORT


def recv(c, out: dict):
    msg = c.receive()
    out.update({"size": msg[0]})
    out.update({"flags": msg[1]})
    out.update({"data": msg[2]})


def echo(client, server, data):
    time.sleep(0.1)
    client.connect(HOST, PORT)
    server_reply = client.send(data)

    msg = server.pop_msg()

    echo_msg = {}
    recv_th = threading.Thread(target=recv, args=[client, echo_msg])
    recv_th.start()

    time.sleep(1)

    client_reply = server.send(msg.client_id, msg.data)

    return server_reply, client_reply, echo_msg


def test_send_text(server, client):
    with open(os.path.join("tests", "dummy_files", "doi.txt"), 'rb') as file:
        text = file.read()

    server_reply, client_reply, msg = echo(client, server, text)
    time.sleep(0.1)

    assert server_reply == (4, 1, len(text))
    assert client_reply == (4, 1, len(text))

    assert msg["size"] == len(text)
    assert msg["flags"] == 2
    assert msg["data"] == text

    client.disconnect()


def test_send_photo(server, client):
    with open(os.path.join("tests", "dummy_files", "photo.jpg"), 'rb') as file:
        photo = file.read()

    server_reply, client_reply, msg = echo(client, server, photo)
    time.sleep(0.1)

    assert server_reply == (4, 1, len(photo))
    assert client_reply == (4, 1, len(photo))

    assert msg["size"] == len(photo)
    assert msg["flags"] == 2
    assert msg["data"] == photo

    client.disconnect()


def test_send_video(server, client):
    buff_size = 16384

    with open(os.path.join("tests", "dummy_files", "video.mp4"), 'rb') as file:
        video = file.read()

    client.set_buff_size(buff_size)
    server.set_default_buff_size(buff_size)

    echo(client, server, video)

    server_reply, client_reply, msg = echo(client, server, video)
    time.sleep(0.1)

    assert server_reply == (4, 1, len(video))
    assert client_reply == (4, 1, len(video))

    assert msg["size"] == len(video)
    assert msg["flags"] == 2
    assert msg["data"] == video

    client.disconnect()
