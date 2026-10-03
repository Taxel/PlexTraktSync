from __future__ import annotations

from plextraktsync.plex.PlexApi import PlexApi
from tests.mock import PlexLibrarySectionMock


class PlexMock(PlexApi):
    def __init__(self, sections):
        self.sections = sections

    def movie_sections(self, library=None):
        by_type = self.sections_by_type("movie", library)
        return by_type

    def show_sections(self, library=None):
        return self.sections_by_type("show", library)

    def sections_by_type(self, libtype, title):
        result = []
        for section in self.sections:
            if section["type"] != libtype:
                continue
            if title and section["title"] != title:
                continue
            result.append(PlexLibrarySectionMock(section))

        return result
