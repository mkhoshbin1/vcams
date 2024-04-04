from sys import stdout
import logging
from pathlib import Path


# self._log_file_path = Path(self.results_path) / (name + '.log')

# Create and configure the logger.
def setup_logger(logger_name: str, log_file: Path,
                 overwrite_logs: bool = True, log_debug: bool = False):
    logger_obj = logging.getLogger(logger_name)
    filemode = 'w' if overwrite_logs else 'a'

    log_level = logging.DEBUG if log_debug else logging.INFO

    # Create file handler and its format.
    file_handler_obj = logging.FileHandler(log_file, filemode)
    file_handler_formatter = logging.Formatter(fmt='%(asctime)s - %(levelname) 5s - %(message)s',
                                               datefmt='%Y-%m-%d %H:%M:%S')
    file_handler_obj.setFormatter(file_handler_formatter)
    logger_obj.addHandler(file_handler_obj)

    stream_handler_obj = logging.StreamHandler(stream=stdout)
    stream_handler_formatter = logging.Formatter(fmt='%(asctime)s - %(levelname) 5s - %(message)s',
                                                 datefmt='%H:%M:%S')
    stream_handler_obj.setFormatter(stream_handler_formatter)
    logger_obj.addHandler(stream_handler_obj)
    logger_obj.setLevel(log_level)

#
# LOG_FORMAT = (
#     "%(asctime)s [%(levelname)s]: %(message)s in %(pathname)s:%(lineno)d")
# LOG_LEVEL = logging.INFO
#
# # Main VoxelPart logger.
# main_logger_file = '/tmp/wasted_meerkats/messaging.log'
#
# main_logger = logging.getLogger('voxelpart_logger.main')
# main_logger.setLevel(LOG_LEVEL)
# messaging_logger_file_handler = FileHandler(MESSAGING_LOG_FILE)
# messaging_logger_file_handler.setLevel(LOG_LEVEL)
# messaging_logger_file_handler.setFormatter(Formatter(LOG_FORMAT))
# main_logger.addHandler(messaging_logger_file_handler)
#
# # payments logger
# PAYMENTS_LOG_FILE = "/tmp/wasted_meerkats/payments.log"
# payments_logger = logging.getLogger("wasted_meerkats.payments")
#
# payments_logger.setLevel(LOG_LEVEL)
# payments_file_handler = FileHandler(PAYMENTS_LOG_FILE)
# payments_file_handler.setLevel(LOG_LEVEL)
# payments_file_handler.setFormatter(Formatter(LOG_FORMAT))
# payments_logger.addHandler(payments_file_handler)
