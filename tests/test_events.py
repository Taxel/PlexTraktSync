#!/usr/bin/env python3 -m pytest
from plextraktsync.watch.EventDispatcher import EventDispatcher
from plextraktsync.watch.EventFactory import EventFactory
from plextraktsync.watch.events import ActivityNotification
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


def test_event_dispatcher():
    raw_events = load_mock("events-played.json")

    events = []
    dispatcher = EventDispatcher().on(
        ActivityNotification, lambda x: events.append(x), event=["ended"]
    )
    dispatcher.event_handler(raw_events[4])
    assert len(events) == 1, "Matched event=ended"

    events = []
    dispatcher = EventDispatcher().on(
        ActivityNotification, lambda x: events.append(x), progress=100
    )
    dispatcher.event_handler(raw_events[4])
    assert len(events) == 1, "Test property progress=100"

    events = []
    dispatcher = EventDispatcher().on(
        ActivityNotification, lambda x: events.append(x), event=["ended"], progress=100
    )
    dispatcher.event_handler(raw_events[4])
    assert len(events) == 1, "Matched event=ended and progress=100"

    events = []
    dispatcher = EventDispatcher().on(
        ActivityNotification,
        lambda x: events.append(x),
        event=["started"],
        progress=100,
    )
    dispatcher.event_handler(raw_events[4])
    assert len(events) == 0, "Matched event=ended and progress=100"

    events = []
    dispatcher = EventDispatcher().on(
        ActivityNotification,
        lambda x: events.append(x),
        progress=100,
        event=["started"],
    )
    dispatcher.event_handler(raw_events[4])
    assert len(events) == 0, "Matched progress=100 and event=started"

    events = []
    dispatcher = EventDispatcher().on(
        ActivityNotification, lambda x: events.append(x), event=["ended"], progress=99
    )
    dispatcher.event_handler(raw_events[4])
    assert len(events) == 0, "No match for event=ended and progress=99"
