from __future__ import annotations

from plextraktsync.decorators.coro import coro
from plextraktsync.factory import factory


@coro
async def update_playlist(playlist: str, remove_watched: bool, dry_run: bool):
    print = factory.print
    pl = playlist
    print(f"Update playlist: '{pl}'")
    print(f"Remove watched from playlist: {remove_watched}")
    print(f"Dry run: {dry_run}")
