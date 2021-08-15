#!/usr/bin/env python3 -m pytest
from unittest.mock import Mock

from plex_trakt_sync.trakt_api import TraktBatch
from tests.conftest import factory, load_mock

trakt = factory.trakt_api()


def test_batch_size_none():
    response = load_mock("trakt_sync_collection_response.json")
    b = TraktBatch(trakt)
    b.trakt_sync_collection = Mock(return_value=response)

    assert b.queue_size() == 0

    request = load_mock("trakt_sync_collection_request.json")
    for media_type, items in request.items():
        for item in items:
            b.add_to_collection(media_type, item)
    assert b.queue_size() == 7

    b.submit_collection()
    assert b.queue_size() == 0
    assert b.trakt_sync_collection.call_count == 1


def test_batch_size_1():
    response = load_mock("trakt_sync_collection_response.json")
    b = TraktBatch(trakt, batch_size=1)
    b.trakt_sync_collection = Mock(return_value=response)

    assert b.queue_size() == 0

    request = load_mock("trakt_sync_collection_request.json")
    for media_type, items in request.items():
        for item in items:
            b.add_to_collection(media_type, item)
    assert b.queue_size() == 0
    assert b.trakt_sync_collection.call_count == 7

    b.submit_collection()
    assert b.queue_size() == 0
    assert b.trakt_sync_collection.call_count == 7
