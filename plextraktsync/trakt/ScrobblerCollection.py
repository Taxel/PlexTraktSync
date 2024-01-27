from __future__ import annotations

from collections import UserDict
from typing import TYPE_CHECKING

from plextraktsync.trakt.ScrobblerProxy import ScrobblerProxy

if TYPE_CHECKING:
    from plextraktsync.trakt.TraktApi import TraktApi
    from plextraktsync.trakt.types import TraktPlayable


class ScrobblerCollection(UserDict):
    def __init__(self, trakt: TraktApi, threshold=80):
        super().__init__()
        self.trakt = trakt
        self.threshold = threshold

    def __missing__(self, media: TraktPlayable):
        scrobbler = media.scrobble(0, None, None)
        self[media] = proxy = ScrobblerProxy(scrobbler, self.threshold)

        return proxy
