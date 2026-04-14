#!/usr/bin/env python3 -m pytest
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from plextraktsync.trakt.TraktWatchedCollection import TraktWatchedCollection


def test_trakt_watched_collection_movies(trakt_api):
    collection = TraktWatchedCollection(trakt_api)
    movies = collection["movies"]
    assert isinstance(movies, dict)


def test_trakt_watched_collection_episodes(trakt_api):
    collection = TraktWatchedCollection(trakt_api)
    episodes = collection["episodes"]
    assert isinstance(episodes, dict)


# Expanded tests below


def test_trakt_watched_collection_movies_with_data():
    # Mock Trakt API with sample watched movies
    mock_trakt = MagicMock()
    mock_movie1 = MagicMock()
    mock_movie1.trakt = 123
    mock_movie2 = MagicMock()
    mock_movie2.trakt = 456
    mock_trakt.me.watched_movies = [mock_movie1, mock_movie2]

    collection = TraktWatchedCollection(mock_trakt)
    movies = collection["movies"]

    assert isinstance(movies, dict)
    assert len(movies) == 2
    assert 123 in movies
    assert 456 in movies
    assert movies[123] is mock_movie1
    assert movies[456] is mock_movie2


def test_trakt_watched_collection_episodes_with_data():
    # Mock Trakt API with sample watched episodes
    mock_trakt = MagicMock()
    mock_episode1 = MagicMock()
    mock_episode1.trakt = 789
    mock_trakt.me.watched_episodes = [mock_episode1]

    collection = TraktWatchedCollection(mock_trakt)
    episodes = collection["episodes"]

    assert isinstance(episodes, dict)
    assert len(episodes) == 1
    assert 789 in episodes
    assert episodes[789] is mock_episode1


def test_trakt_watched_collection_empty():
    # Test with no watched items
    mock_trakt = MagicMock()
    mock_trakt.me.watched_movies = []
    mock_trakt.me.watched_episodes = []

    collection = TraktWatchedCollection(mock_trakt)
    movies = collection["movies"]
    episodes = collection["episodes"]

    assert isinstance(movies, dict)
    assert len(movies) == 0
    assert isinstance(episodes, dict)
    assert len(episodes) == 0


def test_trakt_watched_collection_invalid_media_type():
    mock_trakt = MagicMock()
    collection = TraktWatchedCollection(mock_trakt)

    with pytest.raises(ValueError, match="Unsupported media type: invalid"):
        _ = collection["invalid"]
