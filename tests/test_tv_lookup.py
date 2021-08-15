#!/usr/bin/env python3 -m pytest
from plex_trakt_sync.plex_api import PlexLibraryItem
from tests.conftest import factory, make

trakt = factory.trakt_api()


def test_tv_lookup():
    m = PlexLibraryItem(make(cls='plexapi.video.Show', guid='imdb://tt10584350', type='show'))
    guid = m.guids[0]
    tm = trakt.find_by_guid(guid)
    lookup = trakt.lookup(tm)
    te = lookup[1][2].instance

    assert te.imdb == 'tt12057922', f"Unexpected! {te}"


def test_tv_lookup_by_episode_id():
    pe = PlexLibraryItem(make(
        cls='Episode',
        guid='com.plexapp.agents.thetvdb://77137/1/1?lang=en',
        type='episode',
        seasonNumber=1,
        index=1,
    ))

    guid = pe.guids[0]
    te = trakt.find_by_guid(guid)
    assert te.imdb == "tt0505457"
    assert te.tmdb == 511997


def test_find_episode():
    tm = make(
        cls='TVShow',
        # trakt=4965066,
        trakt=176447,
    )

    pe = PlexLibraryItem(make(
        cls='Episode',
        guid='imdb://tt11909222',
        type='episode',
        seasonNumber=1,
        index=1,
    ))

    guid = pe.guids[0]
    te = trakt.find_episode_guid(tm, guid)
    assert te.season == 1
    assert te.episode == 1
    assert te.imdb == "tt11909222"
