from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from trakt.sync import PlaybackEntry

    from plextraktsync.media.Media import Media


class WatchProgress:
    def __init__(self, progress: list[PlaybackEntry]):
        self.progress = progress

    def match(self, m: Media):
        p = [p for p in self.progress if p == m]
        if not len(p):
            return None
        if len(p) != 1:
            raise RuntimeError(f"Unexpected match count {len(p)}")
        return p[0]
