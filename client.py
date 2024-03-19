import logging

from src.TCPLib.active_client import ActiveTcpClient
from src.TCPLib.passive_client import PassiveTcpClient
import src.TCPLib.logger.logger as log_util
import threading
import time
from tqdm import tqdm
import queue

logger = logging.getLogger()
log_util.config_logger(logger, "Client_Log", logging.DEBUG)

HOST = "127.0.0.1"
PORT = 5000
MESSAGES = queue.Queue()
c_active = ActiveTcpClient(
        HOST,
        PORT,
        MESSAGES
)

c_passive = PassiveTcpClient(
    HOST,
    PORT
)


def active(client):
    client.start()
    while client.is_running():
        msg = MESSAGES.get(block=True)
        print(f"Received {msg.size} bytes")


def passive(client):
    BUFF_SIZE = 1024
    client.connect()
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
