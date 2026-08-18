#!/usr/bin/env python3 -m pytest
"""Integration tests for TraktWatchedCollection using real Trakt API.

These tests validate TraktWatchedCollection against real Trakt API responses.
They are skipped in CI to avoid dependency on external API availability.
Run locally with: pytest tests/test_trakt_watched_collection_integration.py -v
"""

from __future__ import annotations

import os

import pytest

from plextraktsync.trakt.TraktWatchedCollection import TraktWatchedCollection


@pytest.mark.skipif(os.environ.get("CI"), reason="Requires real Trakt API")
def test_trakt_watched_collection_movies(trakt_api):
    """Validate that movies are correctly loaded from real Trakt API."""
    collection = TraktWatchedCollection(trakt_api)
    movies = collection["movies"]
    assert isinstance(movies, dict)


@pytest.mark.skipif(os.environ.get("CI"), reason="Requires real Trakt API")
def test_trakt_watched_collection_episodes(trakt_api):
    """Validate that episodes are correctly loaded from real Trakt API."""
    collection = TraktWatchedCollection(trakt_api)
    episodes = collection["episodes"]
    assert isinstance(episodes, dict)
