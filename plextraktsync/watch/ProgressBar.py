from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

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
        from rich.box import MINIMAL
        from rich.live import Live
        from rich.panel import Panel
        from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

        console = factory.console
        progress = Progress(
            TextColumn(
                " {task.fields[play_state]}  [bold blue]{task.description}",
                justify="left",
            ),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TimeRemainingColumn(),
            console=console,
        )

        # -1 to adjust Kitty terminal issue
        # https://github.com/Textualize/rich/issues/3254#issuecomment-1881885471
        panel_width = console.size.width - 1
        panel = Panel(progress, width=panel_width, padding=(0, 0), box=MINIMAL)
        live = Live(panel, console=console).__enter__()

        def stop():
            progress.stop()
            live.stop()

        import atexit

        atexit.register(lambda: stop())

        return progress

    def __missing__(self, m: PlexLibraryItem):
        self[m] = task = self.progress.add_task(m.title, play_state="")

        return task

    def play(self, m: PlexLibraryItem, progress: float):
        task_id = self[m]
        self.progress.update(
            task_id, completed=progress, play_state=self.ICONS["playing"]
        )

    def pause(self, m: PlexLibraryItem, progress: float):
        task_id = self[m]
        self.progress.update(
            task_id, completed=progress, play_state=self.ICONS["paused"]
        )

    def stop(self, m: PlexLibraryItem):
        task_id = self[m]
        self.progress.remove_task(task_id)
        del self[m]
