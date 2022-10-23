#!/usr/bin/env python3 -m pytest
from trakt.tv import TVShow

from plextraktsync.plex_api import PlexLibraryItem
from plextraktsync.trakt_api import TraktLookup
from tests.conftest import factory, make

trakt = factory.trakt_api()


def test_tv_lookup():
    m = PlexLibraryItem(
        make(cls="plexapi.video.Show", guid="imdb://tt10584350", type="show")
    )
    guid = m.guids[0]
    tm: TVShow = trakt.find_by_guid(guid)
    lookup = TraktLookup(tm)
    te = lookup.from_number(1, 2)

    assert te.imdb == "tt12057922", f"Unexpected! {te}"


def test_show_episodes_plex():
    m = PlexLibraryItem(make(cls="plexapi.video.Show", guid="imdb://tt10584350", type="show"))
    guid = m.guids[0]
    show = trakt.find_by_guid(guid)

    assert len(show.seasons) == 1
    episode = show.seasons[0].episodes[1]
    assert episode.title == "A Murderer's Beef – Part 2"
    assert episode.imdb == "tt12057922", f"Unexpected! {episode}"


def test_show_episodes():
    show = TVShow("Game of Thrones")

    assert len(show.seasons) == 9
    seasons = show.seasons
    episodes = seasons[1].episodes
    assert episodes[0].title == "Winter Is Coming"

    seasons = show.seasons
    assert len(seasons) == 9
    assert seasons[1].episodes[0].title == "Winter Is Coming"


def test_tv_lookup_by_episode_id():
    pe = PlexLibraryItem(
        make(
            cls="Episode",
            guid="com.plexapp.agents.thetvdb://77137/1/1?lang=en",
            type="episode",
            seasonNumber=1,
            index=1,
        )
    )

    guid = pe.guids[0]
    te = trakt.find_by_guid(guid)
    assert te.imdb == "tt0505457"
    assert te.tmdb == 511997


def test_find_episode():
    tm = make(
        cls="TVShow",
        # trakt=4965066,
        trakt=176447,
    )

    pe = PlexLibraryItem(
        make(
            cls="Episode",
            guid="imdb://tt11909222",
            type="episode",
            seasonNumber=1,
            index=1,
        )
    )

    guid = pe.guids[0]
    lookup = trakt.lookup(tm)
    te = trakt.find_episode_guid(guid, lookup)
    assert te.season == 1
    assert te.episode == 1
    assert te.imdb == "tt11909222"


if __name__ == '__main__':
    test_show_episodes()
