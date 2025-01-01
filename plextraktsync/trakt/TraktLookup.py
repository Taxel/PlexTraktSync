from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.decorators.retry import retry
from plextraktsync.factory import logging

EPISODES_ORDERING_WARNING = "episodes ordering is different in Plex and Trakt. " "Check your Plex media source, TMDB is recommended."

if TYPE_CHECKING:
    from trakt.tv import TVEpisode, TVShow

    from plextraktsync.plex.guid.PlexGuid import PlexGuid


class TraktLookup:
    """
    Trakt lookup table to find all Trakt episodes of a TVShow
    """

    logger = logging.getLogger(__name__)

    def __init__(self, tm: TVShow):
        self.provider_table = {}
        self.tm = tm
        self.same_order = True

    @cached_property
    @retry()
    def table(self):
        """
        Build a lookup-table accessible via table[season][episode]

        - https://github.com/moogar0880/PyTrakt/pull/185
        """

        seasons = {}
        for season in self.tm.seasons:
            episodes = {}
            for episode in season.episodes:
                episodes[episode.number] = episode
            seasons[season.season] = episodes
        return seasons

    def _reverse_lookup(self, provider):
        """
        Build a lookup-table accessible via table[provider][id]
        only if episodes ordering is different between Plex and Trakt
        """
        # NB: side effect, assumes that from_number() is called first to populate self.table
        table = {}
        for season in self.table:
            for te in self.table[season].values():
                table[str(te.ids.get(provider))] = te
        self.provider_table[provider] = table
        self.logger.debug(f"{self.tm.title}: lookup table build with '{provider}' ids")

    def from_guid(self, guid: PlexGuid):
        """
        Find Trakt Episode from Guid of Plex Episode
        """
        te = self.from_number(guid.pm.season_number, guid.pm.episode_number)
        if self.invalid_match(guid, te):
            te = self.from_id(guid.provider, guid.id)

        return te

    @staticmethod
    def invalid_match(guid: PlexGuid, episode: TVEpisode | None) -> bool:
        """
        Checks if guid and episode don't match by comparing trakt provided id
        """

        if not episode:
            # nothing to compare with
            return True
        if guid.pm.is_legacy_agent:
            # check can not be performed
            return False
        id_from_trakt = getattr(episode, guid.provider, None)
        return str(id_from_trakt) != guid.id

    def from_number(self, season: int, number: int):
        try:
            return self.table[season][number]
        except KeyError:
            return None

    def from_id(self, provider, id):
        # NB: the code assumes from_id is called only if from_number fails
        if provider not in self.provider_table:
            self._reverse_lookup(provider)
        try:
            ep = self.provider_table[provider][id]
        except KeyError:
            return None
        if self.same_order:
            self.logger.warning(f"'{self.tm.title}' {EPISODES_ORDERING_WARNING}")
            self.same_order = False
        return ep
