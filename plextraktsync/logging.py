import logging
from os.path import join

from .factory import factory
from .path import log_dir


def initialize():
    CONFIG = factory.config()
    # global log level for all messages
    if ("log_debug_messages" in CONFIG and CONFIG["log_debug_messages"]) or CONFIG["logging"]["debug"]:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    log_file = join(log_dir, CONFIG["logging"]["filename"])
    log_format = '%(asctime)s %(levelname)s:%(message)s'

    # messages with info and above are printed to stdout
    console_handler = logging.StreamHandler(factory.progressbar())
    console_handler.terminator = ""
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
        from plexapi import loghandler
        logger.removeHandler(loghandler)
        logger.setLevel(logging.DEBUG)


initialize()
logger = logging.getLogger('PlexTraktSync')
