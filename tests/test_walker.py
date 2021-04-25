#!/usr/bin/env python3 -m pytest
from plex_trakt_sync.walker import Walker
from tests.conftest import get_plex_api, get_media_factory

plex = get_plex_api()
mf = get_media_factory()


def test_walker():
    w = Walker(plex, mf)

    w.add_library("TV Shows")
    w.add_show("Breaking Bad")
    w.add_movie("Batman Begins")
    w.find_episodes()
    w.find_movies()

    assert type(w) == Walker
