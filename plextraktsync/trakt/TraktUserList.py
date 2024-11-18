from __future__ import annotations

from functools import cached_property
from itertools import count
from typing import TYPE_CHECKING

from trakt.users import PublicList

from plextraktsync.factory import factory, logging
from plextraktsync.trakt.types import TraktPlayable

if TYPE_CHECKING:
    from plextraktsync.media.Media import Media
    from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem


class TraktUserList:
    plex_items: list[tuple[int, PlexLibraryItem]]
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        trakt_id: int = None,
        name: str = None,
        items=None,
        keep_watched: bool = None,
    ):
        self.trakt_id = trakt_id
        self.name = name
        self._items = items
        self.description = None
        self.plex_items = []
        self.keep_watched = keep_watched

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __contains__(self, m: Media):
        rank = self.items.get((m.media_type, m.trakt_id))

        return rank is not None

    @property
    def items(self):
        if self._items is None:
            self.description, self._items = self.load_items()
        return self._items

    @staticmethod
    def build_dict(pl: PublicList):
        items = {}
        for le in pl:
            if le.type in ["movie", "episode"]:
                items[(f"{le.type}s", le.trakt)] = le.rank
            elif le.type == "season" and len(le.item.episodes) > 0:
                # Here instead of modifying the ranks of all the items that come after the season,
                # we just assigns float ranks to the episodes based on the season rank.
                # Instead of having some hard coded value, we calculate the rank increment based on the number of episodes.
                # So, in the sorting step, the episodes will be sorted based on the season rank and their position in the season.
                # Example: season rank = 10, number of episodes = 5,
                # episode_rank = 1 / 5 = 0.2
                # episode 1 rank = 10 + (0 * 0.2) = 10.0
                # episode 2 rank = 10 + (1 * 0.2) = 10.2
                # episode 5 rank = 10 + (4 * 0.2) = 10.8
                episode_rank = 1 / len(le.item.episodes)
                for idx, episode in enumerate(le.item.episodes):
                    items[("episodes", episode.trakt)] = le.rank + (idx * episode_rank)
        return items

    def load_items(self):
        pl = PublicList.load(self.trakt_id)
        self.logger.info(f"Downloaded Trakt list '{pl.name}' ({len(pl)} items): {pl.share_link}")

        return pl.description, self.build_dict(pl)

    @classmethod
    def from_trakt_list(cls, list_id: int, list_name: str, keep_watched: bool):
        return cls(trakt_id=list_id, name=list_name, keep_watched=keep_watched)

    @classmethod
    def from_watchlist(cls, items: list[TraktPlayable]):
        trakt_items = dict(zip([(elem.media_type, elem.trakt) for elem in items], count(1)))
        return cls(name="Trakt Watchlist", items=trakt_items)

    @cached_property
    def plex_lists(self):
        return factory.plex_lists

    @cached_property
    def plex_list(self):
        if not self.name:
            raise RuntimeError("Name is required")

        return self.plex_lists[self.name]

    def add(self, m: Media):
        rank = self.items.get((m.media_type, m.trakt_id))
        if rank is None:
            # Item is not in this trakt list
            return

        # TODO: add with rank
        self.plex_items.append((rank, m.plex))

        if m in self.plex_list:
            # Already in the list
            return

        if not self.keep_watched and m.plex.is_watched:
            # Skip adding watched items
            return

        self.logger.info(
            f"Adding {m.title_link} ({m.plex_key}) to Plex list {self.title_link}",
            extra={"markup": True},
        )

        # Report duplicates
        duplicates = [p for _, p in self.plex_items if p.key != m.plex_key and p == m.plex]
        for p in duplicates:
            msg = f"Duplicate {p.title_link} #{p.key} with {m.title_link} #{m.plex_key}"
            if p.edition_title is not None:
                self.logger.info(msg, extra={"markup": True})
            else:
                self.logger.warning(msg, extra={"markup": True})

    @property
    def title_link(self):
        return self.plex_list.title_link

    @property
    def plex_items_sorted(self):
        """
        Returns items sorted by trakt rank

        https://github.com/Taxel/PlexTraktSync/pull/58
        """
        if len(self.plex_items) == 0:
            return []

        plex_items = [(r, p.item) for (r, p) in self.plex_items if self.keep_watched or (not self.keep_watched and not p.is_watched)]
        if len(plex_items) == 0:
            return []

        _, items = zip(*sorted(dict(reversed(plex_items)).items()))

        return items
