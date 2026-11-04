from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Presence:
    """Which watchlists an item was on at a point in time."""

    trakt: bool = False
    plex: bool = False


@dataclass
class WatchlistPlan:
    add_to_plex: set[str] = field(default_factory=set)
    add_to_trakt: set[str] = field(default_factory=set)
    remove_from_plex: set[str] = field(default_factory=set)
    remove_from_trakt: set[str] = field(default_factory=set)
    suppressed_removals: int = 0
    suppress_reason: str | None = None

    @property
    def has_changes(self) -> bool:
        return bool(self.add_to_plex or self.add_to_trakt or self.remove_from_plex or self.remove_from_trakt)

    def drop_removals(self, reason: str) -> None:
        self.suppressed_removals = len(self.remove_from_plex) + len(self.remove_from_trakt)
        if self.suppressed_removals:
            self.suppress_reason = reason
        self.remove_from_plex = set()
        self.remove_from_trakt = set()


def plan_changes(
    previous: dict[str, Presence],
    current: dict[str, Presence],
    *,
    allow_removals: bool,
    suppress_reason: str | None = None,
    max_delete: int | None = None,
) -> WatchlistPlan:
    """Diff the previous synced state against the current state of both watchlists.

    A side's presence flipping absent -> present is an addition on that side, and is
    propagated to the other side. Present -> absent is a removal. An item that was
    absent from a side in *both* states is not actionable there: that is how items
    Plex Discover cannot match stay untouched forever.
    """
    plan = WatchlistPlan()

    for key in set(previous) | set(current):
        was = previous.get(key, Presence())
        now = current.get(key, Presence())

        if now.trakt and not was.trakt and not now.plex:
            plan.add_to_plex.add(key)
        if now.plex and not was.plex and not now.trakt:
            plan.add_to_trakt.add(key)
        if was.trakt and not now.trakt and now.plex:
            plan.remove_from_plex.add(key)
        if was.plex and not now.plex and now.trakt:
            plan.remove_from_trakt.add(key)

    # An item added on one side and removed on the other is ambiguous. Prefer the
    # add: re-adding something the user deleted is recoverable, deleting something
    # they just added is not.
    plan.remove_from_trakt -= plan.add_to_plex
    plan.remove_from_plex -= plan.add_to_trakt

    if not allow_removals:
        plan.drop_removals(suppress_reason or "removals disabled")
        return plan

    if max_delete is not None:
        removals = len(plan.remove_from_plex) + len(plan.remove_from_trakt)
        if removals > max_delete:
            plan.drop_removals(f"{removals} removals exceeds the limit of {max_delete} for this run")

    return plan
