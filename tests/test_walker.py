#!/usr/bin/env python3 -m pytest
from plextraktsync.walker import Walker, WalkConfig
from tests.conftest import factory

plex = factory.plex_api()
trakt = factory.trakt_api()
mf = factory.media_factory()


def test_walker():
    wc = WalkConfig()
    w = Walker(plex, trakt, mf, wc)
    assert type(w) == Walker

    wc.add_library("TV Shows")
    wc.add_library("Movies (Tuti)")
    wc.add_show("Breaking Bad")
    wc.add_movie("Batman Begins")

    episodes = list(w.find_episodes())
    movies = list(w.find_movies())

    assert len(episodes) == 0
    assert len(movies) == 0
