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


def test_event_played():
    event_factory = EventFactory()
    raw_events = load_mock("events-played.json")

    events = [list(event_factory.get_events(data))[0] for data in raw_events]
    assert len(events) == 5
    assert events[0]["event"] == "started"
    assert events[1]["event"] == "updated"
    assert events[4]["event"] == "ended"
    assert events[4]["Activity"]["type"] == "library.refresh.items"
    assert events[4]["Activity"]["progress"] == 100
    assert events[4]["Activity"]["Context"]["key"] == "/library/metadata/513"
