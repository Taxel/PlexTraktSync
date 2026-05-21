#!/usr/bin/env python3 -m pytest
from __future__ import annotations

import pytest
from trakt.errors import OAuthRefreshException

from plextraktsync.queue.BackgroundTask import BackgroundTask
from plextraktsync.watch.FatalErrorState import FatalErrorState
from plextraktsync.watch.WebSocketListener import WebSocketListener


def test_background_task_records_oauth_refresh_exception():
    fatal_error = FatalErrorState()

    def task(_queues):
        raise OAuthRefreshException()

    background_task = BackgroundTask(None, task, fatal_error=fatal_error)
    background_task.timed_events()

    with pytest.raises(OAuthRefreshException):
        fatal_error.raise_if_set()


def test_background_task_continues_without_fatal_error():
    fatal_error = FatalErrorState()
    calls = []

    class Queue:
        def __init__(self):
            self.messages = iter([
                ("test", 1),
                None,
            ])

        def get(self, timeout):
            return next(self.messages)

    def task(queues):
        calls.append(list(queues["test"]))

    background_task = BackgroundTask(None, task, fatal_error=fatal_error)
    background_task(Queue())

    assert calls == [[1]]


def test_websocket_listener_raises_recorded_oauth_refresh_exception(monkeypatch):
    fatal_error = FatalErrorState()

    class Notifier:
        def __init__(self):
            self.calls = 0

        def is_alive(self):
            self.calls += 1
            return self.calls == 1

    class Plex:
        def startAlertListener(self, callback):
            self.callback = callback
            return Notifier()

    def fail_sleep(_interval):
        fatal_error.set(OAuthRefreshException())

    monkeypatch.setattr("plextraktsync.watch.WebSocketListener.sleep", fail_sleep)

    listener = WebSocketListener(Plex(), poll_interval=0, fatal_error=fatal_error)

    with pytest.raises(OAuthRefreshException):
        listener.listen()