from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plexapi.server import PlexServer


class Event(dict):
    def __str__(self):
        return f"{self.__class__}:{str(self.copy())}"


class ServerStarted(Event):
    @property
    def notifier(self):
        return self["notifier"]

    @property
    def server(self) -> PlexServer:
        return self.notifier._server


class Error(Event):
    @property
    def msg(self):
        return self["msg"]


class AccountUpdateNotification(Event):
    pass


class ActivityNotification(Event):
    @property
    def type(self):
        return self["Activity"]["type"]

    @property
    def progress(self):
        return self["Activity"]["progress"]

    @property
    def key(self) -> str:
        return self["Activity"]["Context"]["key"]

    @property
    def event(self):
        return self["event"]


class BackgroundProcessingQueueEventNotification(Event):
    pass


class PlaySessionStateNotification(Event):
    @property
    def key(self):
        return self["key"]

    @property
    def view_offset(self):
        return self["viewOffset"]

    @property
    def state(self):
        return self["state"]

    @property
    def session_key(self):
        return self["sessionKey"]

    @property
    def client_identifier(self):
        return self["clientIdentifier"]


class Setting(Event):
    pass


class ProgressNotification(Event):
    pass


class ReachabilityNotification(Event):
    pass


class StatusNotification(Event):
    pass


class TimelineEntry(Event):
    @property
    def state(self):
        return self["state"]

    @property
    def item_id(self):
        return int(self["itemID"])

    @property
    def metadata_state(self):
        return self["metadataState"]

    @property
    def title(self):
        return self["title"]


class TranscodeSession(Event):
    pass
