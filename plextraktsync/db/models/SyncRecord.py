from __future__ import annotations

from sqlmodel import Field, SQLModel


class SyncRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    media_id: str
    plex_timestamp_watched: str
    seen_on_plex_sync: str
    trakt_timestamp_watched: str
    seen_on_trakt_sync: str
    result: str
