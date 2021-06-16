#!/usr/bin/env python3 -m pytest
from plex_trakt_sync.walker import Walker
from tests.conftest import factory

plex = factory.plex_api()
mf = factory.media_factory()


def test_walker():
    w = Walker(plex, mf)
    assert type(w) == Walker

    w.add_library("TV Shows")
    w.add_library("Movies (Tuti)")
    w.add_show("Breaking Bad")
    w.add_movie("Batman Begins")

    episodes = list(w.find_episodes())
    movies = list(w.find_movies())

    assert len(episodes) == 0
    assert len(movies) == 0
