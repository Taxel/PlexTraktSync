from __future__ import annotations

from plextraktsync.factory import factory
from plextraktsync.watch.events import (ActivityNotification, Error,
                                        PlaySessionStateNotification,
                                        TimelineEntry)


def watch(server: str):
    factory.run_config.update(
        server=server,
    )
    ws = factory.web_socket_listener
    updater = factory.watch_state_updater

    ws.on(
        PlaySessionStateNotification,
        updater.on_play,
        state=["playing", "stopped", "paused"],
    )
    ws.on(
        ActivityNotification,
        updater.on_activity,
        type="library.refresh.items",
        event="ended",
        progress=100,
    )
    ws.on(TimelineEntry, updater.on_delete, state=9, metadata_state="deleted")
    ws.on(Error, updater.on_error)

    ws.listen()
