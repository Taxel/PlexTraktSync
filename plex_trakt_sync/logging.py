import logging
import sys
import tqdm

from .factory import factory
from .path import log_file


class TqdmLoggingHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        super().__init__(stream)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)  



def initialize():
    CONFIG = factory.config()
    # global log level for all messages
    log_level = logging.DEBUG if CONFIG['log_debug_messages'] else logging.INFO
    log_format = '%(asctime)s %(levelname)s:%(message)s'

    # messages with info and above are printed to stdout
    console_handler = TqdmLoggingHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    console_handler.setLevel(logging.INFO)

    # file handler can log down to debug messages
    mode = "a" if CONFIG['logging']['append'] else "w"
    file_handler = logging.FileHandler(log_file, mode, 'utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)-15s %(levelname)s[%(name)s]:%(message)s"))
    file_handler.setLevel(logging.DEBUG)

    handlers = [
        file_handler,
        console_handler,
    ]
    logging.basicConfig(format=log_format, handlers=handlers, level=log_level)

    # Set debug for other components as well
    if log_level == logging.DEBUG:
        from plexapi import log as logger
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)


initialize()
logger = logging.getLogger('PlexTraktSync')
