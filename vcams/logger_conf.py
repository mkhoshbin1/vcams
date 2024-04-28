from sys import stdout
import logging
from pathlib import Path


def setup_main_logger(log_file: Path, display_log: bool = False,
                      overwrite_logs: bool = True, log_debug: bool = False):
    """TODO: doc"""
    logger_name = 'vcams'  # This will become the root for all library-level logs.
    logger_obj = logging.getLogger(logger_name)
    filemode = 'w' if overwrite_logs else 'a'

    log_level = logging.DEBUG if log_debug else logging.INFO

    # Create file handler and its format.
    file_handler_obj = logging.FileHandler(log_file, filemode)
    file_handler_formatter = logging.Formatter(fmt='%(asctime)s - %(levelname) 5s - %(message)s',
                                               datefmt='%Y-%m-%d %H:%M:%S')
    file_handler_obj.setFormatter(file_handler_formatter)
    logger_obj.addHandler(file_handler_obj)

    if display_log:
        stream_handler_obj = logging.StreamHandler(stream=stdout)
        stream_handler_formatter = logging.Formatter(fmt='%(asctime)s - %(levelname) 5s - %(message)s',
                                                     datefmt='%H:%M:%S')
        stream_handler_obj.setFormatter(stream_handler_formatter)
        logger_obj.addHandler(stream_handler_obj)
    logger_obj.setLevel(log_level)


def setup_dispersion_logger(part_name: str, log_file: Path, display_log: bool = False,
                            overwrite_logs: bool = True):
    """TODO: doc"""
    logger_name = part_name + '_dispersion_log'
    logger_obj = logging.getLogger(logger_name)
    filemode = 'w' if overwrite_logs else 'a'

    # Create file handler and its format.
    file_handler_obj = logging.FileHandler(log_file, filemode)
    file_handler_obj.terminator = ''
    file_handler_formatter = logging.Formatter(fmt='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
    file_handler_obj.setFormatter(file_handler_formatter)
    logger_obj.addHandler(file_handler_obj)

    if display_log:
        stream_handler_obj = logging.StreamHandler(stream=stdout)
        stream_handler_obj.terminator = ''
        stream_handler_formatter = logging.Formatter(fmt='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        stream_handler_obj.setFormatter(stream_handler_formatter)
        logger_obj.addHandler(stream_handler_obj)
    logger_obj.setLevel(logging.DEBUG)

    # Log creation of the object.
    logger_obj.debug(f"Starting shape dispersion in part '{part_name}'.\n\n")
    return logger_obj


class LogWithoutFormatContext():
    # See Python Logging Cookbook.
    bare_handler_formatter = logging.Formatter(fmt='')

    def __init__(self, logger_obj):  # , level=None, handler=None, close=True):
        self.logger_obj = logger_obj
        self.old_formatter_list = []

    def __enter__(self):
        for hndlr in self.logger_obj.handlers:
            self.old_formatter_list.append(hndlr.formatter)
            hndlr.setFormatter(self.bare_handler_formatter)

    def __exit__(self, et, ev, tb):
        for hndlr in self.logger_obj.handlers:
            hndlr.setFormatter(self.old_formatter_list.pop(0))

# def log_without_format(logger_obj, handler_class=None):
# bare_handler_formatter = logging.Formatter(fmt='')
# for hndlr in logger_obj.handlers:
#     if (handler_class is None) or isinstance(hndlr, handler_class):
#         old_formatter = hndlr.formatter
#         hndlr.setFormatter(bare_handler_formatter)
#         logger_obj.debug('sadsfg')
#         hndlr.setFormatter(old_formatter)
