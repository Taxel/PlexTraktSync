from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.coro import coro
from plextraktsync.factory import factory
from plextraktsync.plex.PlexPlaylist import PlexPlaylist

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
    print(f"Update playlist: '{playlist}'")
    print(f"Remove watched from playlist: {remove_watched}")
    print(f"Dry run: {dry_run}")

    pl = PlexPlaylist(factory.plex_server, playlist)
    print(f"Playlist: {pl}")
    items = pl.playlist.items().copy()
    p: PlexPlayable
    for p in items:
        if remove_watched and p.isPlayed:
            print(f"{'Remove' if not dry_run else 'Would remove'} from playlist: {format_title(p)}")
            items.remove(p)
    print(f"Update playlist: {len(pl)} -> {len(items)} items")
    if not dry_run:
        pl.update(items)
