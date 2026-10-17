#!/usr/bin/env python3 -m pytest
"""Unit tests for TraktWatchedCollection with mocked Trakt API responses.

These tests use MagicMock to simulate Trakt API responses without making
real API calls. They run in CI and provide fast, reliable test coverage.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from plextraktsync.trakt.TraktWatchedCollection import TraktWatchedCollection


def test_trakt_watched_collection_movies_with_sample_data():
    """Test movies are correctly indexed by trakt ID using sample Trakt API data."""
    # Mock Trakt API with real-world sample watched movies
    # Sample structure: Trakt API returns watched movies with trakt ID and metadata
    mock_trakt = MagicMock()

    # Create mock movies using real-world-like structure
    mock_movie1 = MagicMock()
    mock_movie1.trakt = 278  # The Shawshank Redemption
    mock_movie1.title = "The Shawshank Redemption"
    mock_movie1.year = 1994

    mock_movie2 = MagicMock()
    mock_movie2.trakt = 278945  # Inception
    mock_movie2.title = "Inception"
    mock_movie2.year = 2010

    # Configure mock API to return these movies
    mock_trakt.me.watched_movies = [mock_movie1, mock_movie2]

    collection = TraktWatchedCollection(mock_trakt)
    movies = collection["movies"]

    # Verify structure and content match expected behavior
    assert isinstance(movies, dict)
    assert len(movies) == 2
    assert 278 in movies
    assert 278945 in movies
    assert movies[278] is mock_movie1
    assert movies[278945] is mock_movie2


def test_trakt_watched_collection_episodes_with_sample_data():
    """Test episodes are correctly indexed by trakt ID using sample Trakt API data."""
    # Mock Trakt API with real-world sample watched episodes
    mock_trakt = MagicMock()

    # Create mock episodes using real-world-like structure
    # Episodes typically have: trakt ID, show info, season, number, etc.
    mock_episode1 = MagicMock()
    mock_episode1.trakt = 73641  # Game of Thrones S01E01
    mock_episode1.show = MagicMock()
    mock_episode1.show.title = "Game of Thrones"
    mock_episode1.season = 1
    mock_episode1.number = 1

    mock_episode2 = MagicMock()
    mock_episode2.trakt = 73642  # Game of Thrones S01E02
    mock_episode2.show = MagicMock()
    mock_episode2.show.title = "Game of Thrones"
    mock_episode2.season = 1
    mock_episode2.number = 2

    # Configure mock API to return these episodes
    mock_trakt.me.watched_episodes = [mock_episode1, mock_episode2]

    collection = TraktWatchedCollection(mock_trakt)
    episodes = collection["episodes"]

    # Verify structure and content match expected behavior
    assert isinstance(episodes, dict)
    assert len(episodes) == 2
    assert 73641 in episodes
    assert 73642 in episodes
    assert episodes[73641] is mock_episode1
    assert episodes[73642] is mock_episode2


def test_trakt_watched_collection_empty():
    """Test handling of empty watched collections."""
    # Mock Trakt API with no watched items
    mock_trakt = MagicMock()
    mock_trakt.me.watched_movies = []
    mock_trakt.me.watched_episodes = []

    collection = TraktWatchedCollection(mock_trakt)
    movies = collection["movies"]
    episodes = collection["episodes"]

    # Verify empty dicts are returned correctly
    assert isinstance(movies, dict)
    assert len(movies) == 0
    assert isinstance(episodes, dict)
    assert len(episodes) == 0


def test_trakt_watched_collection_invalid_media_type():
    """Test that unsupported media types raise appropriate errors."""
    mock_trakt = MagicMock()
    collection = TraktWatchedCollection(mock_trakt)

    # Verify only "movies" and "episodes" are supported
    with pytest.raises(ValueError, match="Unsupported media type: invalid"):
        _ = collection["invalid"]

    # Verify other unsupported types also fail
    with pytest.raises(ValueError, match="Unsupported media type: shows"):
        _ = collection["shows"]
