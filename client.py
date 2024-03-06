from src.TCPLib.active_client import ActiveTcpClient, DEBUG
from src.TCPLib.passive_client import PassiveTcpClient
import threading
import time
from tqdm import tqdm
import queue

HOST = "127.0.0.1"
PORT = 5000
MESSAGES = queue.Queue()
c_active = ActiveTcpClient(
        HOST,
        PORT,
        MESSAGES,
        logging_level=DEBUG,
        log_path="C:\\Users\\Josh\\PycharmProjects\\TCPLib\\client_log.txt"
    )

c_passive = PassiveTcpClient(HOST, PORT)


def active(client):
    client.start()
    while MESSAGES.empty():
        time.sleep(0.1)
    msg = MESSAGES.get()
    print(msg.data)
    client.stop()


def passive(client):
    BUFF_SIZE = 1024
    client.connect(HOST, PORT)
    data = bytearray()
    gen = client.receive(BUFF_SIZE)
    try:
        size, flags = next(gen)
    except StopIteration as e:
        print(e)
        return
    print(f"Receiving {size} bytes")
    total_iter = int(size / BUFF_SIZE)
    for chunk in tqdm(gen, total=total_iter):
        data.extend(chunk)
    print(f"Completed receiving {size} bytes")


    # size, data = client.receive_all(4096)
    # print(f"Size = {size} | Bytes Recv = {len(data)}")

    client.disconnect()


passive(c_passive)
# active(c_active)
#
