import time
import os

from tests.fixtures import server, a_client, HOST, PORT


def echo(client, server, data, client_msg_q):
    time.sleep(0.1)
    client_id = server.list_clients()[0]
    client.send(data)

    server_copy = server.pop_msg(block=True)
    server.send(client_id, server_copy.data)

    client_copy = client_msg_q.get(block=True)

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


def test_send_text(server, a_client):
    with open(os.path.abspath(os.path.join("tests", "dummy_files", "DOI.txt")), 'rb') as file:
        text = file.read()
    client = a_client[0]
    client_msgs = a_client[1]
    server_msg, client_msg = echo(client, server, text, client_msgs)

    assert server_msg["size"] == len(text)
    assert server_msg["flags"] == 2
    assert server_msg["data"] == text

    assert client_msg["size"] == len(text)
    assert client_msg["flags"] == 2
    assert client_msg["data"] == text


def test_send_photo(server, a_client):
    with open(os.path.abspath(os.path.join("tests", "dummy_files", "photo.jpg")), 'rb') as file:
        photo = file.read()

    client = a_client[0]
    client_msgs = a_client[1]
    server_msg, client_msg = echo(client, server, photo, client_msgs)

    assert server_msg["size"] == len(photo)
    assert server_msg["flags"] == 2
    assert server_msg["data"] == photo

    assert client_msg["size"] == len(photo)
    assert client_msg["flags"] == 2
    assert client_msg["data"] == photo


def test_send_video(server, a_client):
    with open(os.path.abspath(os.path.join("tests", "dummy_files", "video.mp4")), 'rb') as file:
        video = file.read()

    client = a_client[0]
    client_msgs = a_client[1]
    server_msg, client_msg = echo(client, server, video, client_msgs)

    assert server_msg["size"] == len(video)
    assert server_msg["flags"] == 2
    assert server_msg["data"] == video

    assert client_msg["size"] == len(video)
    assert client_msg["flags"] == 2
    assert client_msg["data"] == video
