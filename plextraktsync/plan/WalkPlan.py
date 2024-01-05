from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from plexapi.video import Episode, Movie, Show

    from plextraktsync.plex.PlexLibrarySection import PlexLibrarySection


class WalkPlan(NamedTuple):
    movie_sections: list[PlexLibrarySection]
    show_sections: list[PlexLibrarySection]
    movies: list[Movie]
    shows: list[Show]
    episodes: list[Episode]
