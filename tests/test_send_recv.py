import time
import os

from tests.fixtures import server, a_client, HOST, PORT


def echo(client, server, data, client_msg_q):
    time.sleep(0.1)
    client_id = server.list_clients()[0]
    client.send(data)

    server_copy = server.pop_msg(block=True)
    server_reply = client_msg_q.get(block=True)
    server.send(client_id, server_copy.data)

    client_copy = client_msg_q.get(block=True)
    client_reply = server.pop_msg(block=True)

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

    server_reply = {
        "size": server_reply.size,
        "flags": server_reply.flags,
        "data": server_reply.data
    }

    client_reply = {
        "size": client_reply.size,
        "flags": client_reply.flags,
        "data": client_reply.data
    }

    return server_copy, client_copy, server_reply, client_reply


def test_send_text(server, a_client):
    with open(os.path.abspath(os.path.join("tests", "dummy_files", "DOI.txt")), 'rb') as file:
        text = file.read()
    client = a_client[0]
    client_msgs = a_client[1]
    server_msg, client_msg, server_reply, client_reply = echo(client, server, text, client_msgs)

    assert server_msg["size"] == len(text)
    assert server_msg["flags"] == 2
    assert server_msg["data"] == text

    assert client_msg["size"] == len(text)
    assert client_msg["flags"] == 2
    assert client_msg["data"] == text

    assert server_reply["size"] == 4
    assert server_reply["flags"] == 1
    assert server_reply["data"] == int.to_bytes(len(text), byteorder='big', length=4)

    assert client_reply["size"] == 4
    assert client_reply["flags"] == 1
    assert client_reply["data"] == int.to_bytes(len(text), byteorder='big', length=4)


def test_send_photo(server, a_client):
    with open(os.path.abspath(os.path.join("tests", "dummy_files", "photo.jpg")), 'rb') as file:
        photo = file.read()

    client = a_client[0]
    client_msgs = a_client[1]
    server_msg, client_msg, server_reply, client_reply = echo(client, server, photo, client_msgs)

    assert server_msg["size"] == len(photo)
    assert server_msg["flags"] == 2
    assert server_msg["data"] == photo

    assert client_msg["size"] == len(photo)
    assert client_msg["flags"] == 2
    assert client_msg["data"] == photo

    assert server_reply["size"] == 4
    assert server_reply["flags"] == 1
    assert server_reply["data"] == int.to_bytes(len(photo), byteorder='big', length=4)

    assert client_reply["size"] == 4
    assert client_reply["flags"] == 1
    assert client_reply["data"] == int.to_bytes(len(photo), byteorder='big', length=4)


def test_send_video(server, a_client):
    with open(os.path.abspath(os.path.join("tests", "dummy_files", "video.mp4")), 'rb') as file:
        video = file.read()

    client = a_client[0]
    client_msgs = a_client[1]
    server_msg, client_msg, server_reply, client_reply = echo(client, server, video, client_msgs)

    assert server_msg["size"] == len(video)
    assert server_msg["flags"] == 2
    assert server_msg["data"] == video

    assert client_msg["size"] == len(video)
    assert client_msg["flags"] == 2
    assert client_msg["data"] == video

    assert server_reply["size"] == 4
    assert server_reply["flags"] == 1
    assert server_reply["data"] == int.to_bytes(len(video), byteorder='big', length=4)

    assert client_reply["size"] == 4
    assert client_reply["flags"] == 1
    assert client_reply["data"] == int.to_bytes(len(video), byteorder='big', length=4)
