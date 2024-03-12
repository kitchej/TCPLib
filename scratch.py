import time
import traceback
import queue

from src.TCPLib.tcp_server import TCPServer
from src.TCPLib.active_client import ActiveTcpClient


a = ActiveTcpClient("127.0.0.1", 5000, queue.Queue())
print(__name__)