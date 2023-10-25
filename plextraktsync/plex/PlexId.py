from __future__ import annotations

from dataclasses import dataclass


@dataclass(unsafe_hash=True)
class PlexId:
    key: int | str
    media_type: str = None
    provider: str = None
    server: str = None

    METADATA = "metadata.provider.plex.tv"
    METADATA_URL = "https://metadata.provider.plex.tv/library/metadata"

    @property
    def plex(self):
        from plextraktsync.factory import factory

        if not self.server:
            return factory.plex_api

        return factory.get_plex_by_id(self.server)

    @property
    def metadata_url(self):
        return f"{self.METADATA_URL}/{self.key}"

    @property
    def is_discover(self):
        return self.provider == self.METADATA

    def __repr__(self):
        keys = [self.__class__.__name__, self.server, self.provider, self.key]
        fields = map(str, filter(None, keys))

        return f'<{":".join(fields)}>'
