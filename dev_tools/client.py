import logging
import time

from src.TCPLib.active_client import ActiveTcpClient
from src.TCPLib.passive_client import PassiveTcpClient
import dev_tools.log_util as log_util
from tqdm import tqdm
import queue
import threading

logger = logging.getLogger()
log_util.add_file_handler(logger, "logs\\Client_Log", logging.DEBUG, "TCPLibFileHandler")
log_util.add_stream_handler(logger, logging.DEBUG, "TCPLibStreamHander")

HOST = "127.0.0.1"
PORT = 5000

# HOST = "192.168.1.32"
# PORT = 5000
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


def client_list(num_clients):
    clients = [PassiveTcpClient(host=HOST, port=PORT) for _ in range(num_clients)]
    return  clients


def active(client):
    client.start()
    while client.is_running():
        msg = MESSAGES.get(block=True)


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
    total_iter = int(size / BUFF_SIZE)
    for chunk in tqdm(gen, total=total_iter):
        data.extend(chunk)

    # size, data = client.receive_all(4096)
    # print(f"Size = {size} | Bytes Recv = {len(data)}")

    client.disconnect()


def multi_client():
    clients = client_list(10)
    threads = []
    for c in clients:
        c.connect()
        threads.append(threading.Thread(target=c.send, args=[b"Hello World"]))

    for thread in threads:
        thread.start()

    time.sleep(1)

    for c in clients:
        c.disconnect()


# passive(c_passive)
# active(c_active)
multi_client()
