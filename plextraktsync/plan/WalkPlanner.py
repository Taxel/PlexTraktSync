from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from plextraktsync.plan.WalkPlan import WalkPlan

if TYPE_CHECKING:
    from plextraktsync.plan.WalkConfig import WalkConfig
    from plextraktsync.plex.PlexApi import PlexApi


class WalkPlanner:
    def __init__(self, plex: PlexApi, config: WalkConfig):
        self.plex = plex
        self.config = config

    def plan(self):
        movie_sections, show_sections = self.find_sections()
        movies, shows, episodes = self.find_by_id(movie_sections, show_sections)
        shows = self.find_from_sections_by_title(show_sections, self.config.show, shows)
        movies = self.find_from_sections_by_title(movie_sections, self.config.movie, movies)

        # reset sections if movie/shows have been picked
        if movies or shows or episodes:
            movie_sections = []
            show_sections = []

        return WalkPlan(
            movie_sections,
            show_sections,
            movies,
            shows,
            episodes,
        )

    def find_by_id(self, movie_sections, show_sections):
        if not self.config.id:
            return [None, None, None]

        results = defaultdict(list)
        for id in self.config.id:
            found = self.find_from_sections_by_id(show_sections, id, results) if self.config.walk_shows else None
            if found:
                continue
            found = self.find_from_sections_by_id(movie_sections, id, results) if self.config.walk_movies else None
            if found:
                continue
            raise RuntimeError(f"Id '{id}' not found")

        movies = []
        shows = []
        episodes = []
        for mediatype, items in results.items():
            if mediatype == "episode":
                episodes.extend(items)
            elif mediatype == "show":
                shows.extend(items)
            elif mediatype == "movie":
                movies.extend(items)
            else:
                raise RuntimeError(f"Unsupported type: {mediatype}")

        return [movies, shows, episodes]

    @staticmethod
    def find_from_sections_by_id(sections, id, results):
        for section in sections:
            m = section.find_by_id(id)
            if m:
                results[m.type].append(m)
                return True
        return False

    @staticmethod
    def find_from_sections_by_title(sections, names, items):
        if not names:
            return items

        if not items:
            items = []

        for name in names:
            found = False
            for section in sections:
                m = section.find_by_title(name)
                if m:
                    items.append(m)
                    found = True
            if not found:
                raise RuntimeError(f"Show/Movie '{name}' not found")

        return items

    def find_sections(self):
        """
        Build movie and show sections based on library and walk_movies/walk_shows.
        A valid match must be found if such filter is enabled.

        :return: [movie_sections, show_sections]
        """
        if not self.config.library:
            movie_sections = self.plex.movie_sections() if self.config.walk_movies else []
            show_sections = self.plex.show_sections() if self.config.walk_shows else []
            return [movie_sections, show_sections]

        movie_sections = []
        show_sections = []
        for library in self.config.library:
            movie_section = self.plex.movie_sections(library) if self.config.walk_movies else []
            if movie_section:
                movie_sections.extend(movie_section)
                continue
            show_section = self.plex.show_sections(library) if self.config.walk_shows else []
            if show_section:
                show_sections.extend(show_section)
                continue
            raise RuntimeError(f"Library '{library}' not found")

        return [movie_sections, show_sections]
