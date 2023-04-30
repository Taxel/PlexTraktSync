from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Session, select

from plextraktsync.db.models.SyncRecord import SyncRecord

if TYPE_CHECKING:
    from sqlalchemy.future import Engine

    from plextraktsync.media import Media


class SyncDatabase:
    def __init__(self, engine: Engine):
        self.engine = engine

    def find_by_id(self, media_type: str, trakt_id: int):
        with Session(self.engine) as session:
            statement = (
                select(SyncRecord)
                .where(SyncRecord.media_type == media_type)
                .where(SyncRecord.trakt_id == trakt_id)
            )
            return session.exec(statement).first()

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
