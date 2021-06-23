#!/usr/bin/env python3 -m pytest
from plex_trakt_sync.events import EventFactory
from tests.conftest import load_mock


def test_events():
    event_factory = EventFactory()
    data = load_mock("events.json")

    events = event_factory.get_events(data)
    for event in events:
        assert event["event"] == "ended"
        assert event["Activity"]["progress"] == 100
