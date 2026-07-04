#!/usr/bin/env python3 -m pytest
from __future__ import annotations

import pytest
from trakt.tv import TVShow

from plextraktsync.pytrakt_extensions import AllShowsProgress, ShowProgress
from plextraktsync.trakt.TraktApi import TraktApi
from tests.conftest import factory

trakt: TraktApi = factory.trakt_api


@pytest.mark.skip(reason="Broken in CI")
def test_trakt_watched_progress():
    show = TVShow("Game of Thrones")
    data = show.watched_progress()
    watched = ShowProgress(**data)

    assert isinstance(watched, ShowProgress)
    s01e01 = watched.get_completed(1, 1)
    assert isinstance(s01e01, bool)


def test_show_progress_with_missing_seasons():
    """Trakt can return a show entry without a "seasons" key (e.g. shows with
    zero watched progress). This should not raise TypeError: 'NoneType' object
    is not iterable. Regression test for #2515."""
    show = {"show": {"ids": {"trakt": 1, "slug": "some-show"}}}
    prog = ShowProgress(**show)

    assert isinstance(prog, ShowProgress)
    assert prog.seasons == {}
    assert prog.completed is False


def test_all_shows_progress_with_missing_shows():
    """Trakt's /sync/watched/shows can return null instead of an empty list.
    This should not raise TypeError: 'NoneType' object is not iterable.
    Regression test for #2515."""
    progress = AllShowsProgress(shows=None)

    assert isinstance(progress, AllShowsProgress)
    assert progress.shows == {}


if __name__ == "__main__":
    test_trakt_watched_progress()
    test_show_progress_with_missing_seasons()
    test_all_shows_progress_with_missing_shows()
