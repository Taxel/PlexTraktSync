#!/usr/bin/env python3 -m pytest

from plextraktsync.factory import logger


def test_logger():
    logger.info("Log plain text")
    logger.info(["log object"])
    logger.info([{"a": "some object"}])

    # with some markup
    logger.info(["[link=https://app.plex.tv/][green]test[/][/] tested"])
