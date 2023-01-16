from __future__ import annotations

from collections import UserDict
from typing import TYPE_CHECKING

from plextraktsync.trakt.ScrobblerProxy import ScrobblerProxy

if TYPE_CHECKING:
    from typing import Union

    from plexapi.video import Movie
    from trakt.tv import TVEpisode

    from plextraktsync.trakt.TraktApi import TraktApi


class ScrobblerCollection(UserDict):
    def __init__(self, trakt: TraktApi, threshold=80):
        super().__init__()
        self.trakt = trakt
        self.threshold = threshold

    def __missing__(self, media: Union[Movie, TVEpisode]):
        scrobbler = media.scrobble(0, None, None)
        proxy = ScrobblerProxy(scrobbler, self.threshold)
        self[media] = proxy

        return proxy
