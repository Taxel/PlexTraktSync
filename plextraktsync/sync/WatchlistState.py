from __future__ import annotations

import json
from datetime import datetime, timezone
from os import path, replace

from plextraktsync.factory import logging

from .WatchlistMirror import Presence

SCHEMA_VERSION = 1


class WatchlistState:
    """Snapshot of the watchlist state after the previous successful sync.

    Stored as JSON next to config.yml, keyed by a scope so that two Plex servers
    sharing one Trakt account do not overwrite each other's state.

    Anything unexpected - a missing file, unreadable JSON, an unknown schema
    version, an unknown scope - reads as "not seeded". The caller is expected to
    treat that as "seed this run, delete nothing", because losing this file must
    never be able to empty a watchlist.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, state_path: str, scope: str):
        self.path = state_path
        self.scope = scope
        self._seeded = False
        self._unresolved = 0

    @property
    def is_seeded(self) -> bool:
        return self._seeded

    @property
    def unresolved_baseline(self) -> int:
        """How many Plex watchlist entries failed to resolve during the last sync.

        Some entries can never resolve - Trakt simply has no record of that GUID.
        Those are a permanent, harmless shortfall, so treating any shortfall as a
        failed enumeration would disable removals forever on such an account.
        Recording the count makes the check self-calibrating: only a shortfall
        *worse* than last time indicates something actually went wrong.
        """
        return self._unresolved

    def _read_document(self) -> dict:
        if not path.exists(self.path):
            return {}

        try:
            with open(self.path, encoding="utf-8") as fp:
                document = json.load(fp)
        except (OSError, ValueError) as e:
            self.logger.warning(f"Ignoring unreadable watchlist state at {self.path}: {e}")
            return {}

        if not isinstance(document, dict) or document.get("version") != SCHEMA_VERSION:
            self.logger.warning(f"Ignoring watchlist state at {self.path}: unsupported schema version")
            return {}

        return document

    def load(self) -> tuple[dict[str, Presence], str | None]:
        entry = (self._read_document().get("scopes") or {}).get(self.scope)
        if not entry:
            self._seeded = False
            self._unresolved = 0
            return {}, None

        items = {key: Presence(trakt=bool(value.get("trakt")), plex=bool(value.get("plex"))) for key, value in (entry.get("items") or {}).items()}
        self._seeded = True
        self._unresolved = int(entry.get("unresolved") or 0)

        return items, entry.get("synced_at")

    def save(self, items: dict[str, Presence], unresolved: int = 0) -> None:
        document = self._read_document() or {"version": SCHEMA_VERSION, "scopes": {}}
        document.setdefault("scopes", {})[self.scope] = {
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "unresolved": unresolved,
            "items": {key: {"trakt": presence.trakt, "plex": presence.plex} for key, presence in items.items()},
        }

        tmp = f"{self.path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fp:
            json.dump(document, fp, indent=2, sort_keys=True)
        replace(tmp, self.path)

        self._seeded = True
        self._unresolved = unresolved
