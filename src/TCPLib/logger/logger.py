"""
logger.py
Written by Joshua Kitchen - 2024

NOTE: This module was intended to be used for developing and debugging the module. If you want the library to log
messages, you must create and configure a root logger in your application with logging.getLogger().
This is all you have to do, The library will automatically get and log messages to your logger.
"""

import logging
import sys

DEBUG_FORMATTER = logging.Formatter(
    '%(asctime)s - %(name)s.%(funcName)s on %(threadName)s - %(levelname)s : %(message)s',
    "%m/%d/%Y %I:%M:%S %p"
)

INFO_FORMATTER = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s : %(message)s',
    "%m/%d/%Y %I:%M:%S %p"
)


def config_logger(logger, log_path, log_level):
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.set_name("TCPLibFileHandler")
    file_handler.setLevel(log_level)

    if log_level == logging.DEBUG:
        formatter = DEBUG_FORMATTER
    elif log_level == logging.INFO:
        formatter = INFO_FORMATTER
    else:
        formatter = DEBUG_FORMATTER

    file_handler.setFormatter(formatter)
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
