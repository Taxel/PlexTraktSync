#!/usr/bin/env python3 -m pytest
from unittest.mock import Mock

from plextraktsync.trakt_api import TraktBatch
from tests.conftest import factory, load_mock

trakt = factory.trakt_api


def test_batch_delay_none():
    response = load_mock("trakt_sync_collection_response.json")
    b = TraktBatch(trakt, "collection", add=True)
    b.trakt_sync = Mock(return_value=response)

    assert b.queue_size() == 0

    request = load_mock("trakt_sync_collection_request.json")
    for media_type, items in request.items():
        for item in items:
            b.add_to_items(media_type, item)
    assert b.queue_size() == 7

    b.submit()
    assert b.queue_size() == 0
    assert b.trakt_sync.call_count == 1


def test_batch_delay_1():
    response = load_mock("trakt_sync_collection_response.json")
    b = TraktBatch(trakt, "collection", add=True, batch_delay=1)
    b.trakt_sync = Mock(return_value=response)

    assert b.queue_size() == 0

    request = load_mock("trakt_sync_collection_request.json")
    for media_type, items in request.items():
        for item in items:
            b.add_to_items(media_type, item)
    assert b.queue_size() == 7
    assert b.trakt_sync.call_count == 0

    b.submit()
    assert b.queue_size() == 0
    assert b.trakt_sync.call_count == 1
