import logging
from pathlib import Path
from sys import stdout

from vcams.helper import process_working_dir


def setup_main_logger(part_name: str, working_dir: str | Path,
                      display_log: bool = True, overwrite_logs: bool = True,
                      log_debug: bool = False) -> Path:
    """Set up the main logger for a *VoxelPart* object and return its file Path."""
    logger_name = 'vcams'  # This will become the root for all library-level logs.
    logger_obj = logging.getLogger(logger_name)
    filemode = 'w' if overwrite_logs else 'a'
    # Process and Validate working_dir.
    # This may be the second time that this is done, but it's OK.
    working_dir = process_working_dir(working_dir, part_name)
    log_file_path = Path(working_dir) / (part_name + '.log')  # Make sure it's necessary.

    log_level = logging.DEBUG if log_debug else logging.INFO

    # Create file handler and its format.
    file_handler_obj = logging.FileHandler(log_file_path, filemode)
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
    return log_file_path


def setup_dispersion_logger(part_name: str, log_file: Path, display_log: bool = False,
                            overwrite_logs: bool = True):
    """Set up the dispersion logger for a *ShapeDispersionArray* instance defined for a *VoxelPart* instance."""
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


class LogWithoutFormatContext:
    """A context manager that allows logging to happen without any formatting.
    It saves each handler's formatter, sets it to an empty one and restores it when exiting.
    """
    # See https://docs.python.org/3/howto/logging-cookbook.html#using-a-context-manager-for-selective-logging
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
