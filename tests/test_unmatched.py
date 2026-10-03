#!/usr/bin/env python3 -m pytest
from __future__ import annotations

import pytest

from plextraktsync.commands.unmatched import select_libraries
from plextraktsync.plan.WalkConfig import WalkConfig
from plextraktsync.plan.Walker import Walker
from tests.mock import PlexMock

SECTIONS = [
    {"type": "movie", "title": "Movies", "items": []},
    {"type": "movie", "title": "Old Movies", "items": []},
    {"type": "show", "title": "TV Shows", "items": []},
]


def make_walker():
    return Walker(plex=PlexMock(SECTIONS), trakt=None, mf=None, config=WalkConfig())


def titles(walker):
    return [s.data["title"] for s in walker.plan.movie_sections]


def test_explicit_library():
    walker = make_walker()
    select_libraries(walker, ("Old Movies",))
    assert titles(walker) == ["Old Movies"]


def test_multiple_libraries():
    walker = make_walker()
    select_libraries(walker, ("Old Movies", "Movies"))
    assert titles(walker) == ["Old Movies", "Movies"]


def test_no_library_keeps_all_movie_sections():
    walker = make_walker()
    select_libraries(walker, ())
    assert titles(walker) == ["Movies", "Old Movies"]


def test_nonexistent_library():
    walker = make_walker()
    with pytest.raises(RuntimeError, match="Library 'Missing' not found"):
        select_libraries(walker, ("Missing",))


def test_non_movie_library():
    walker = make_walker()
    with pytest.raises(RuntimeError, match="not a movie library"):
        select_libraries(walker, ("TV Shows",))
