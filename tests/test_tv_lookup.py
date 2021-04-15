#!/usr/bin/env python3 -m pytest
from plex_trakt_sync.plex_api import PlexLibraryItem
from plex_trakt_sync.trakt_api import TraktApi


def make(cls=None, **kwargs):
    cls = cls if cls is not None else "object"
    # https://stackoverflow.com/a/2827726/2314626
    return type(cls, (object,), kwargs)


trakt = TraktApi()


def test_tv_lookup():
    m = PlexLibraryItem(make(cls='plexapi.video.Show', guid='imdb://tt10584350', type='show'))
    tm = trakt.find_movie(m)
    lookup = trakt.lookup(tm)
    te = lookup[1][2].instance

    assert te.imdb == 'tt12057922', f"Unexpected! {te}"
