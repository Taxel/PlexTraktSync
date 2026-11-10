#!/usr/bin/env python3 -m pytest
from __future__ import annotations

from trakt.movies import Movie
from trakt.tv import TVEpisode, TVSeason, TVShow

from plextraktsync.media.Media import Media


def make_show():
    return TVShow(
        title="Brickleberry",
        ids={"trakt": 1, "slug": "brickleberry", "imdb": "tt1", "tmdb": 2, "tvdb": 3},
    )


def test_trakt_url_movie():
    movie = Movie(title="Inception", year=2010, ids={"trakt": 5, "slug": "inception-2010", "imdb": "tt123"})
    m = Media(plex=None, trakt=movie)

    assert m.trakt_url == "https://app.trakt.tv/movies/inception-2010"


def test_trakt_url_movie_without_slug():
    movie = Movie(title="Inception", year=2010, ids={"trakt": 5})
    m = Media(plex=None, trakt=movie)

    assert m.trakt_url == f"https://app.trakt.tv/movies/{m.trakt_id}"


def test_trakt_url_show():
    show = make_show()
    m = Media(plex=None, trakt=show)

    assert m.trakt_url == "https://app.trakt.tv/shows/brickleberry"


def test_trakt_url_season():
    show = make_show()
    season = TVSeason(show.title, 2, show.slug, episode_count=0)
    m = Media(plex=None, trakt=season)

    assert m.trakt_url == "https://app.trakt.tv/shows/brickleberry/seasons/2"


def test_trakt_url_episode_with_show_object():
    show = make_show()
    episode = TVEpisode(show=show.title, season=2, number=3, show_id=show.trakt, ids={"trakt": 99})
    # Mirrors TraktApi.find_by_episode_guid, which overwrites the "show" attribute
    # with the actual TVShow instance instead of the plain title string.
    episode.show = show

    m = Media(plex=None, trakt=episode)

    assert m.trakt_url == "https://app.trakt.tv/shows/brickleberry?season=2&view=episode&episode=3"


def test_trakt_url_episode_without_show_object():
    episode = TVEpisode(show="Brickleberry", season=2, number=3, show_id=42, ids={"trakt": 99})
    m = Media(plex=None, trakt=episode)

    assert m.trakt_url == "https://app.trakt.tv/shows/42?season=2&view=episode&episode=3"


def test_trakt_url_episode_without_show_id_falls_back_to_show_title():
    # No show object and no show_id: only the show title is left. The episode id
    # must never end up in the show path.
    episode = TVEpisode(show="Brickleberry", season=2, number=3, ids={"trakt": 99})
    m = Media(plex=None, trakt=episode)

    assert m.trakt_url == "https://app.trakt.tv/shows/brickleberry?season=2&view=episode&episode=3"


def test_trakt_url_episode_with_unknown_show():
    # Nothing identifies the parent show, no url rather than a wrong one.
    episode = TVEpisode(show="", season=2, number=3, ids={"trakt": 99})
    m = Media(plex=None, trakt=episode)

    assert m.trakt_url is None
