from dataclasses import dataclass


@dataclass
class SyncRecord:
    media_id: str
    plex_timestamp_watched: str
    seen_on_plex_sync: str
    trakt_timestamp_watched: str
    seen_on_trakt_sync: str
    result: str

    id: str = None
