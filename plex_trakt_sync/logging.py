import logging
import sys
from .config import CONFIG
from .path import log_file


def initialize():
    # global log level for all messages
    log_level = logging.DEBUG if CONFIG['log_debug_messages'] else logging.INFO
    log_format = '%(asctime)s %(levelname)s:%(message)s'

    # messages with info and above are printed to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    console_handler.setLevel(logging.INFO)

    # file handler can log down to debug messages
    file_handler = logging.FileHandler(log_file, 'w', 'utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)-15s %(levelname)s[%(name)s]:%(message)s"))
    file_handler.setLevel(logging.DEBUG)

    handlers = [
        file_handler,
        console_handler,
    ]
    logging.basicConfig(format=log_format, handlers=handlers, level=log_level)


initialize()

logger = logging.getLogger('PlexTraktSync')
