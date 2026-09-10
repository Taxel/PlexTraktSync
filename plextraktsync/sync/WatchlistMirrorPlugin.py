from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import logging
from plextraktsync.plugin import hookimpl

from .WatchlistMirror import Presence, plan_changes

if TYPE_CHECKING:
    from plextraktsync.media.Media import Media
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.trakt.TraktApi import TraktApi

    from .plugin.SyncPluginInterface import Sync, SyncConfig, SyncPluginManager, Walker
    from .WatchlistMirror import WatchlistPlan
    from .WatchlistState import WatchlistState


class WatchlistMirrorPlugin:
    """Two-way watchlist sync that propagates removals.

    Unlike WatchListPlugin, this keeps a snapshot of the state after the previous
    sync. That is what makes "on Trakt but not on Plex" decidable: it is an
    addition on Trakt if it was not on Trakt last time, and a removal on Plex if
    it was on Plex last time. Without that record the two cases are identical and
    the only safe guess is "addition", which is why removals otherwise come back.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, plex: PlexApi, trakt: TraktApi, state: WatchlistState, max_delete_percent: int):
        self.plex = plex
        self.trakt = trakt
        self.state = state
        self.max_delete_percent = max_delete_percent

    @staticmethod
    def enabled(config: SyncConfig):
        return config.watchlist_mirror

    @classmethod
    def factory(cls, sync: Sync):
        from plextraktsync.path import watchlist_state

        from .WatchlistState import WatchlistState

        return cls(
            plex=sync.plex,
            trakt=sync.trakt,
            state=WatchlistState(watchlist_state, scope=f"{sync.plex.config.id}|{sync.trakt.me.username}"),
            max_delete_percent=sync.config.watchlist_mirror_max_delete_percent,
        )

    @hookimpl
    def init(self, pm: SyncPluginManager, is_partial: bool):
        if not is_partial:
            return

        self.logger.warning("Disabling Watchlist Mirror: Running partial library sync")
        pm.unregister(self)

    @cached_property
    def plex_wl(self):
        from plextraktsync.plex.PlexWatchList import PlexWatchList

        return PlexWatchList(self.plex.watchlist())

    @cached_property
    def trakt_wl(self):
        return self.trakt.watchlist_movies + self.trakt.watchlist_shows

    @hookimpl
    async def fini(self, walker: Walker, dry_run: bool):
        if not walker.config.walk_watchlist:
            return

        with measure_time("Mirrored watchlist"):
            await self.mirror_watchlist(walker, dry_run=dry_run)

    async def mirror_watchlist(self, walker: Walker, dry_run: bool):
        # Both sides are measured before anything is mutated: the legacy plugin
        # deletes matched entries out of its Trakt collection as it walks, and a
        # diff taken afterwards would be against a list that no longer reflects
        # what is really on Trakt.
        plex_total = len(self.plex_wl)
        trakt_total = len(self.trakt_wl)

        media: dict[str, Media] = {}
        current: dict[str, Presence] = {}
        resolved_from_plex = 0

        async for m in walker.media_from_plexlist(self.plex_wl):
            resolved_from_plex += 1
            key = self.key(m)
            media[key] = m
            current[key] = Presence(trakt=False, plex=True)

        async for m in walker.media_from_traktlist(self.trakt_wl):
            key = self.key(m)
            media.setdefault(key, m)
            current[key] = Presence(trakt=True, plex=current.get(key, Presence()).plex)

        previous, _ = self.state.load()
        allow_removals, reason = self.removal_gate(plex_total, trakt_total, resolved_from_plex)
        max_delete = max(1, len(previous) * self.max_delete_percent // 100) if previous else None

        plan = plan_changes(
            previous,
            current,
            allow_removals=allow_removals,
            suppress_reason=reason,
            max_delete=max_delete,
        )

        if plan.suppressed_removals:
            self.logger.warning(f"Skipping {plan.suppressed_removals} watchlist removal(s): {plan.suppress_reason}")

        self.apply(plan, media, dry_run=dry_run)

        # Only a completed pass may become the new baseline. Recording state from
        # a run that raised partway would bake a false "this was removed" into the
        # next diff.
        if not dry_run:
            self.state.save(current)

    def removal_gate(self, plex_total: int, trakt_total: int, resolved_from_plex: int) -> tuple[bool, str | None]:
        """Decide whether removals may be applied at all this run.

        Every branch here answers the same question: could this run's view of a
        watchlist be wrong? If so, absence is not evidence of removal, and only
        additions are safe.
        """
        if not self.state.is_seeded:
            return False, "first run, seeding watchlist state"
        if plex_total == 0:
            return False, "Plex watchlist came back empty, treating as a failed fetch"
        if trakt_total == 0:
            return False, "Trakt watchlist came back empty, treating as a failed fetch"
        if resolved_from_plex < plex_total:
            missing = plex_total - resolved_from_plex
            return False, f"{missing} Plex watchlist item(s) could not be matched, so absence is not proof of removal"

        return True, None

    @staticmethod
    def key(m: Media) -> str:
        # Trakt ids are unique only within a media type, and the two watchlists
        # are walked into one namespace. Plex rating keys are deliberately not
        # used: Plex Discover reissues them for the same title, which a snapshot
        # would read as a delete plus an unrelated add.
        return f"{m.media_type}:{m.trakt_id}"

    def apply(self, plan: WatchlistPlan, media: dict[str, Media], dry_run: bool):
        for key in sorted(plan.add_to_plex):
            m = media[key]
            if m.plex is None:
                self.logger.info(f"Skipping {m.title_link} from Trakt watchlist because not found in Plex Discover", extra={"markup": True})
                continue
            self.logger.info(f"Adding {m.title_link} to Plex watchlist", extra={"markup": True})
            if not dry_run:
                m.add_to_plex_watchlist()

        for key in sorted(plan.add_to_trakt):
            m = media[key]
            self.logger.info(f"Adding {m.title_link} to Trakt watchlist", extra={"markup": True})
            if not dry_run:
                m.add_to_trakt_watchlist()

        for key in sorted(plan.remove_from_plex):
            m = media[key]
            if m.plex is None:
                continue
            self.logger.info(f"Removing {m.title_link} from Plex watchlist", extra={"markup": True})
            if not dry_run:
                m.remove_from_plex_watchlist()

        for key in sorted(plan.remove_from_trakt):
            m = media[key]
            self.logger.info(f"Removing {m.title_link} from Trakt watchlist", extra={"markup": True})
            if not dry_run:
                m.remove_from_trakt_watchlist()
