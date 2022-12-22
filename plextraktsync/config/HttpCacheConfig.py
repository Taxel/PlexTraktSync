from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from requests_cache import DO_NOT_CACHE

if TYPE_CHECKING:
    from requests_cache import ExpirationPatterns

# 3 Months
LONG_EXPIRY = timedelta(weeks=4 * 3)


@dataclass(frozen=True)
class HttpCacheConfig:
    """
    Http Cache config dataclass
    """

    policy: ExpirationPatterns

    default_policy = {
        # Requests matching these patterns will not be cached
        "*.trakt.tv/shows/*/seasons": DO_NOT_CACHE,
        "*.trakt.tv/sync/collection/shows": DO_NOT_CACHE,
        "*.trakt.tv/sync/watched/shows": DO_NOT_CACHE,
        "*.trakt.tv/users/*/collection/movies": DO_NOT_CACHE,
        "*.trakt.tv/users/*/collection/shows": DO_NOT_CACHE,
        "*.trakt.tv/users/*/ratings/*": DO_NOT_CACHE,
        "*.trakt.tv/users/*/watched/movies": DO_NOT_CACHE,
        "*.trakt.tv/users/*/watchlist/movies": DO_NOT_CACHE,
        "*.trakt.tv/users/*/watchlist/shows": DO_NOT_CACHE,
        "*.trakt.tv/users/likes/lists": DO_NOT_CACHE,
        "*.trakt.tv/users/me": DO_NOT_CACHE,

        # Online Plex patterns
        "metadata.provider.plex.tv/library/metadata/*/userState": DO_NOT_CACHE,
        "metadata.provider.plex.tv/library/metadata/*?*includeUserState=1": DO_NOT_CACHE,
        "metadata.provider.plex.tv/library/metadata/*": LONG_EXPIRY,
        "metadata.provider.plex.tv/library/sections/watchlist/all": DO_NOT_CACHE,
        # plex account
        "plex.tv/users/account": DO_NOT_CACHE,

        # Plex patterns
        # Ratings search
        "*/library/sections/*/all?*userRating%3E%3E=-1*": DO_NOT_CACHE,
        # len(PlexLibrarySection)
        "*/library/sections/*/all?includeCollections=0&X-Plex-Container-Size=0&X-Plex-Container-Start=0": DO_NOT_CACHE,
        # __iter__(PlexLibrarySection)
        "*/library/sections/*/all?includeGuids=1": DO_NOT_CACHE,
        # find_by_title
        "*/library/sections/*/all?includeGuids=1&title=*": DO_NOT_CACHE,
        # fetch_item, fetch_items
        "*/library/sections/*/all?*": DO_NOT_CACHE,
        "*/library/sections/*/collections": DO_NOT_CACHE,
        # library_sections
        "*/library/sections": DO_NOT_CACHE,

        # reloads
        "*/library/metadata/*?*include*": DO_NOT_CACHE,
        # episodes
        "*/library/metadata/*/allLeaves": DO_NOT_CACHE,
        # find_by_id
        "*/library/metadata/*": DO_NOT_CACHE,
        # mark played, mark unplayed
        "*/:/scrobble?key=*&identifier=com.plexapp.plugins.library": DO_NOT_CACHE,
        "*/:/unscrobble?key=&&identifier=com.plexapp.plugins.library": DO_NOT_CACHE,
        # playlists
        "*/playlists?title=": DO_NOT_CACHE,
        "*/playlists/*/items": DO_NOT_CACHE,
        "*/library": DO_NOT_CACHE,
        # history
        "*/status/sessions/history/all": DO_NOT_CACHE,
        # has_sessions
        "*/status/sessions": DO_NOT_CACHE,
        # system_device
        "*/devices": DO_NOT_CACHE,
        # system_account
        "*/accounts": DO_NOT_CACHE,
        # version, updated_at
        # "*/": DO_NOT_CACHE,
    }

    @property
    def urls_expire_after(self) -> ExpirationPatterns:
        """
        Create url patterns:
        - https://requests-cache.readthedocs.io/en/stable/examples.html#url-patterns
        - https://requests-cache.readthedocs.io/en/stable/user_guide/expiration.html#url-patterns

        NOTE: If there is more than one match, the first match will be used in the order they are defined
        """

        # We need to build the dict manually, so users can have overrides for builtin patterns
        policy = {}
        for k, v in self.default_policy.items():
            # Use user value if present
            if k in self.policy:
                v = self.policy[k]
            policy[k] = v

        policy.update(self.policy)

        return policy

    def serialize(self):
        return {
            "http_cache": {
                "policy": self.urls_expire_after,
            },
        }

    def dump(self, print=None):
        """
        Print config serialized as yaml.
        If print is None, return the produced string instead.
        """
        from plextraktsync.config.ConfigLoader import ConfigLoader
        data = self.serialize()
        dump = ConfigLoader.dump_yaml(None, data)
        if print is None:
            return dump
        print(dump)
