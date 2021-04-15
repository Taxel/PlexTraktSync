#!/usr/bin/env python3 -m pytest
import pytest
from trakt.errors import MethodNotAllowedException

from plex_trakt_sync.plex_api import PlexLibraryItem
from plex_trakt_sync.trakt_api import TraktApi


def make(cls=None, **kwargs):
    cls = cls if cls is not None else "object"
    # https://stackoverflow.com/a/2827726/2314626
    return type(cls, (object,), kwargs)


trakt = TraktApi()


def test_tv_lookup():
    m = PlexLibraryItem(make(cls='plexapi.video.Show', guid='imdb://tt10584350', type='show'))
    tm = trakt.find_by_media(m)
    lookup = trakt.lookup(tm)
    te = lookup[1][2].instance

    assert te.imdb == 'tt12057922', f"Unexpected! {te}"


def test_tv_lookup_by_episode_id2():
    pe = PlexLibraryItem(make(
        cls='Episode',
        guid='com.plexapp.agents.thetvdb://77137/1/1?lang=en',
        type='episode',
        seasonNumber=1,
        index=1,
    ))

    with pytest.raises(MethodNotAllowedException):
        trakt.find_by_media(pe)


def test_tv_lookup_by_episode_id3():
    pm = PlexLibraryItem(make(
        cls='Show',
        guid='com.plexapp.agents.thetvdb://77137?lang=en',
        type='show',
        trakt=13948,
    ))
    pe = PlexLibraryItem(make(
        cls='Episode',
        guid='com.plexapp.agents.thetvdb://77137/1/1?lang=en',
        type='episode',
        seasonNumber=1,
        index=1,
    ))
    te = trakt.find_episode(pe, pm)

    assert te.imdb == 'tt0505457', f"Unexpected! {te}"
