from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel


class SyncRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    media_type: str
    trakt_id: int
    plex_timestamp_watched: str
    seen_on_plex_sync: str
    trakt_timestamp_watched: str
    seen_on_trakt_sync: str
