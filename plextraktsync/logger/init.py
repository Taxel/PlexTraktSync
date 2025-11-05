from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler

from plextraktsync.factory import factory


def initialize(config):
    # global log level for all messages
    log_level = logging.DEBUG if config.log_debug else logging.INFO

    # messages with info and above are printed to stdout
    console_handler = factory.console_logger
    console_handler.terminator = ""
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    console_handler.setLevel(logging.INFO)

    # file handler can log down to debug messages
    mode = "a" if config.log_append else "w"
    log_rotation = config.log_rotation
    log_rotation_max_bytes = config.log_rotation_max_bytes
    log_rotation_backup_count = config.log_rotation_backup_count
    if log_rotation:
        file_handler = RotatingFileHandler(config.log_file, mode, log_rotation_max_bytes, log_rotation_backup_count, "utf-8")
    else:
        file_handler = logging.FileHandler(config.log_file, mode, "utf-8")
    file_handler.setFormatter(CustomFormatter("%(asctime)-15s %(levelname)s[%(name)s]:%(message)s"))
    file_handler.setLevel(logging.DEBUG)

    handlers = [
        file_handler,
        console_handler,
    ]
    logging.basicConfig(handlers=handlers, level=log_level, force=True)

    # Set debug for other components as well
    if log_level == logging.DEBUG:
        from plexapi import log as logger
        from plexapi import loghandler

        logger.removeHandler(loghandler)
        logger.setLevel(logging.DEBUG)


class CustomFormatter(logging.Formatter):
    MARKUP_PATTERN = re.compile(r"\[link=[^\]]*\]|(\[green\])|(\[\/\])")

    def formatMessage(self, record):
        record.message = self.remove_markup(record.message)
        return super().formatMessage(record)

    @classmethod
    def remove_markup(cls, text: str) -> str:
        return cls.MARKUP_PATTERN.sub("", text)
