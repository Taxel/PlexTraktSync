#!/usr/bin/env python3 -m pytest
from __future__ import annotations

from plextraktsync.factory import logging


def test_logger():
    logger = logging.getLogger(__name__)
    logger.info("Log plain text")
    logger.info(["log object"])
    logger.info([{"a": "some object"}])

    # with some markup
    logger.info(["[link=https://app.plex.tv/][green]test[/][/] tested"])
