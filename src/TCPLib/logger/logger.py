import logging
import sys


class LogLevels:
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    ERROR = logging.ERROR


def config_logger(logger, log_path, log_level):
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.set_name("TCPLibFileHandler")
    file_handler.setLevel(log_level)

    file_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s : %(message)s',
            "%m/%d/%Y %I:%M:%S %p"
        )
    )

    logger.addHandler(file_handler)
    logger.setLevel(log_level)


def toggle_stream_handler(logger, log_level):
    for handler in logger.handlers:
        if handler.name == "TCPLibStreamHandler":
            logger.removeHandler(handler)
            return

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.set_name("TCPLibStreamHandler")
    stream_handler.setLevel(log_level)

    stream_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s : %(message)s',
            "%m/%d/%Y %I:%M:%S %p"
        )
    )

    logger.addHandler(stream_handler)
