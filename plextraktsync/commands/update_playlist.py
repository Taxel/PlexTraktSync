from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.coro import coro
from plextraktsync.factory import factory

if TYPE_CHECKING:
    from plextraktsync.plex.types import PlexPlayable


def format_title(p: PlexPlayable):
    library_title = p._data.attrib.get("librarySectionTitle")
    title = f"'{p.title}'"
    if p.year:
        title += f" ({p.year})"

    if library_title:
        title += f" (in '{library_title}')"
    if p.sourceURI:
        title += f" (on {p.sourceURI})"

    return title


@coro
async def update_playlist(playlist: str, remove_watched: bool, dry_run: bool):
    print = factory.print
    pl = playlist
    print(f"Update playlist: '{pl}'")
    print(f"Remove watched from playlist: {remove_watched}")
    print(f"Dry run: {dry_run}")
