#!/usr/bin/env python3 -m pytest
from __future__ import annotations

from trakt.tv import TVShow

from plextraktsync.pytrakt_extensions import ShowProgress
from plextraktsync.trakt.TraktApi import TraktApi
from tests.conftest import factory, skip_in_ci

trakt: TraktApi = factory.trakt_api


@skip_in_ci
def test_trakt_watched_progress():
    show = TVShow("Game of Thrones")
    data = show.watched_progress()
    watched = ShowProgress(**data)

    assert isinstance(watched, ShowProgress)
    s01e01 = watched.get_completed(1, 1)
    assert isinstance(s01e01, bool)


if __name__ == "__main__":
    test_trakt_watched_progress()
