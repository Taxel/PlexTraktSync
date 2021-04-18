#!/usr/bin/env python3 -m pytest
from plex_trakt_sync.walker import Walker


def test_walker():
    w = Walker()

    w.add_library("TV Shows")
    w.add_show("Breaking Bad")
    w.add_movie("Batman Begins")
    w.find_episodes()
    w.find_movies()

    assert type(w) == Walker
