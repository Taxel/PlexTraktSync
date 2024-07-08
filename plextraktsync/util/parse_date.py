from __future__ import annotations

from datetime import timedelta

from pytimeparse import parse


def parse_date(date: str):
    return timedelta(seconds=parse(date))
