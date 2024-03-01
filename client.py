import TCPLib.TCPClient as TCPClient
import threading
import time
from tqdm import tqdm

HOST = "127.0.0.1"
PORT = 5000

c = TCPClient.TCPClient(
        HOST,
        PORT,
        logging_level=TCPClient.DEBUG,
        log_path="C:\\Users\\Josh\\PycharmProjects\\TCPLib\\client_log.txt"
    )


def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


BUFF_SIZE = 1024

c.connect(HOST, PORT)

data = bytearray()
gen = c.receive(BUFF_SIZE)

size, flags = next(gen)
print(f"Receiving {size} bytes")
total_iter = int(size / BUFF_SIZE)
for chunk in tqdm(gen, total=total_iter):
    data.extend(chunk)
print(f"Completed receiving {size} bytes")

c.disconnect()

# size, data = c.receive_all(4096)
# print(f"Size = {size} | Bytes Recv = {len(data)}")

