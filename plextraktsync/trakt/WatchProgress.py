from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from trakt.sync import PlaybackEntry


class WatchProgress:
    def __init__(self, progress: list[PlaybackEntry]):
        self.progress = progress
