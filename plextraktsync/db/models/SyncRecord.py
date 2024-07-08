from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Column, DateTime, func, text


class SyncRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    media_type: str
    trakt_id: int
    created_at: datetime = Field(
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
        }
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(), onupdate=func.now())
    )
    plex_timestamp_watched: str
    seen_on_plex_sync: str
    trakt_timestamp_watched: str
    seen_on_trakt_sync: str
