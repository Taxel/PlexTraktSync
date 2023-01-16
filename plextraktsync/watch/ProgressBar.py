from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.factory import factory

if TYPE_CHECKING:
    from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem


class ProgressBar(dict):
    ICONS = {
        "playing": "▶️",
        "paused": "⏸️",
    }

    @cached_property
    def progress(self):
        from rich.progress import (BarColumn, Progress, TextColumn,
                                   TimeRemainingColumn)

        progress = Progress(
            TextColumn("{task.fields[play_state]}  [bold blue]{task.description}", justify="left"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TimeRemainingColumn(),
            console=factory.console,
        )
        progress.start()

        import atexit
        atexit.register(lambda: progress.stop())

        return progress

    def __missing__(self, m: PlexLibraryItem):
        task = self.progress.add_task(m.title, play_state="")
        self[m] = task

        return task

    def play(self, m: PlexLibraryItem, progress: float):
        task_id = self[m]
        self.progress.update(task_id, completed=progress, play_state=self.ICONS["playing"])

    def pause(self, m: PlexLibraryItem, progress: float):
        task_id = self[m]
        self.progress.update(task_id, completed=progress, play_state=self.ICONS["paused"])

    def stop(self, m: PlexLibraryItem):
        task_id = self[m]
        self.progress.remove_task(task_id)
        del self[m]
