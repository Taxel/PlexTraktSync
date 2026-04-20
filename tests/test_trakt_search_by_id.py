#!/usr/bin/env python3 -m pytest
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from plextraktsync.trakt.TraktApi import TraktApi


def make_trakt_item(media_type: str, id_type: str, media_id: str):
    """Return a minimal mock Trakt search-result item."""
    item = MagicMock()
    item.media_type = media_type
    item.ids = {"ids": {id_type: media_id}}
    return item


@pytest.fixture
def trakt_api():
    # Patch the module-level `factory` imported by TraktApi to avoid
    # real HTTP session creation during __init__.
    with patch("plextraktsync.trakt.TraktApi.factory") as mock_factory:
        mock_factory.session = MagicMock()
        yield TraktApi()


def test_search_by_id_type_mismatch_returns_none(trakt_api):
    """When the API returns an item whose type differs from the requested type, return None."""
    # Requested "movie" but API returned a "shows" result.
    item = make_trakt_item(media_type="shows", id_type="tmdb", media_id="12345")
    with patch("trakt.sync.search_by_id", return_value=[item]):
        result = trakt_api.search_by_id("12345", id_type="tmdb", media_type="movie")
    assert result is None


def test_search_by_id_id_mismatch_returns_none(trakt_api):
    """When the API returns an item whose id differs from the requested id, return None."""
    # Requested id "12345" but API returned an item with id "99999".
    item = make_trakt_item(media_type="movies", id_type="tmdb", media_id="99999")
    with patch("trakt.sync.search_by_id", return_value=[item]):
        result = trakt_api.search_by_id("12345", id_type="tmdb", media_type="movie")
    assert result is None


def test_search_by_id_matching_returns_item(trakt_api):
    """When the API returns an item whose type and id both match, return that item."""
    item = make_trakt_item(media_type="movies", id_type="tmdb", media_id="12345")
    with patch("trakt.sync.search_by_id", return_value=[item]):
        result = trakt_api.search_by_id("12345", id_type="tmdb", media_type="movie")
    assert result is item
