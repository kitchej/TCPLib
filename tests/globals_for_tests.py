import os
import shutil

HOST = "127.0.0.1"
PORT = 5000


def setup_log_folder(folder_name):
    if not os.path.exists("logs"):
        os.mkdir("logs")
    log_folder = os.path.join("logs", folder_name)
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
    else:
        shutil.rmtree(log_folder)
        os.mkdir(log_folder)
    return log_folder
