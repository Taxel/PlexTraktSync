from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.db.Database import Database
from plextraktsync.db.SyncRecord import SyncRecord

if TYPE_CHECKING:
    from plextraktsync.media import Media


class SyncDatabase:
    table_name = "sync"
    # fields:
    # A. Media ID
    # B. Plex timestamp watched
    # C. seen on Plex sync?
    # D. Trakt timestamp watched
    # E. seen on Trakt sync?
    # F. result
    schema = """
        id PRIMARY KEY,
        media_id,
        plex_timestamp_watched,
        seen_on_plex_sync,
        trakt_timestamp_watched,
        seen_on_trakt_sync,
        result
    """

    def __init__(self, con: Database):
        self.con = con
        with self.con as con:
            self._create_table(con)

    # Initial CREATE TABLE must happen in shared connection; subsequent queries will use thread-local connections
    def _create_table(self, con: Database):
        con.execute(f'CREATE TABLE IF NOT EXISTS {self.table_name} ({self.schema})')

    def insert(self, record: SyncRecord):
        pass

    def update(self, m: Media):
        record = SyncRecord(
            media_id=m.trakt_id,
            plex_timestamp_watched=m.watched_on_plex,
            seen_on_plex_sync=m.watched_on_plex,
            trakt_timestamp_watched=m.watched_on_trakt,
            seen_on_trakt_sync=m.watched_on_trakt,
            result="",
        )
        print(record)
