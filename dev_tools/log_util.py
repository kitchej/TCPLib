"""
log_util.py
Written by Joshua Kitchen - 2024

NOTE: This module was intended to be used for developing and debugging the library. If you want the library to log
messages, you must create and configure a root logger in your application. This is all you have to do, as the library
will automatically get and log messages to your logger.
"""

import logging
import sys

DEBUG_FORMATTER = logging.Formatter(
    '%(asctime)s - %(module)s.%(funcName)s on %(threadName)s - %(levelname)s :\n %(message)s\n',
    "%m/%d/%Y %I:%M:%S %p"
)

INFO_FORMATTER = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s :\n %(message)s\n',
    "%m/%d/%Y %I:%M:%S %p"
)


def add_file_handler(logger, log_path, log_level, handler_name):
    for handler in logger.handlers:
        if handler.name == handler_name:
            logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.set_name(handler_name)
    file_handler.setLevel(log_level)

    if log_level == logging.DEBUG:
        formatter = DEBUG_FORMATTER
    elif log_level == logging.INFO:
        formatter = INFO_FORMATTER
    else:
        formatter = DEBUG_FORMATTER

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def add_stream_handler(logger, log_level, handler_name):
    for handler in logger.handlers:
        if handler.name == handler_name:
            logger.removeHandler(handler)
            return

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.set_name(handler_name)
    stream_handler.setLevel(log_level)

    if log_level == logging.DEBUG:
        formatter = DEBUG_FORMATTER
    elif log_level == logging.INFO:
        formatter = INFO_FORMATTER
    else:
        formatter = DEBUG_FORMATTER

    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
