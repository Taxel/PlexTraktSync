from __future__ import annotations

from typing import TYPE_CHECKING

from plexapi.exceptions import NotFound

from plextraktsync.decorators.retry import retry
from plextraktsync.rich.RichMarkup import RichMarkup

if TYPE_CHECKING:
    from typing import Literal

    from plexapi.library import MovieSection, ShowSection

    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.types import PlexMedia


class PlexLibrarySection(RichMarkup):
    def __init__(self, section: ShowSection | MovieSection, plex: PlexApi = None):
        self.section = section
        self.plex = plex

    def pager(self, libtype: Literal["episode"] = None):
        from plextraktsync.plex.PlexSectionPager import PlexSectionPager

        return PlexSectionPager(section=self.section, plex=self.plex, libtype=libtype)

    @property
    def type(self):
        return self.section.type

    @property
    def title(self):
        return self.section.title

    @property
    def link(self):
        """Return Plex App URL for this section"""
        base_url = self.plex.plex_base_url("media")

        return f"{base_url}/com.plexapp.plugins.library?source={self.section.key}"

    @property
    def title_link(self):
        return self.markup_link(self.link, self.title)

    def find_by_title(self, name: str):
        try:
            return self.section.get(name)
        except NotFound:
            return None

    @retry
    def search(self, **kwargs):
        return self.section.search(**kwargs)

    def find_by_id(self, id: str | int) -> PlexMedia | None:
        try:
            return self.section.fetchItem(int(id))
        except NotFound:
            return None

    def __repr__(self):
        return f"<{self.__class__.__name__}:{self.type}:{self.title}>"
