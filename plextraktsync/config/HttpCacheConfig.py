from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from requests_cache import DO_NOT_CACHE, EXPIRE_IMMEDIATELY, NEVER_EXPIRE

from plextraktsync.util.parse_date import parse_date

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

    # Special values for expiry patterns
    expire_constants = {
        "DO_NOT_CACHE": DO_NOT_CACHE,
        "EXPIRE_IMMEDIATELY": EXPIRE_IMMEDIATELY,
        "NEVER_EXPIRE": NEVER_EXPIRE,
    }

    default_policy = {
        "api.trakt.tv/shows/*/seasons?extended=episodes": 28800,
        "api.trakt.tv/shows/*/seasons": DO_NOT_CACHE,
        "api.trakt.tv/sync/collection/shows": "1m",
        "api.trakt.tv/users/*/collection/movies?extended=metadata": "10s",
        "api.trakt.tv/users/*/collection/movies": DO_NOT_CACHE,
        "api.trakt.tv/users/*/collection/shows": "1m",
        "api.trakt.tv/users/*/ratings/episodes": "10s",
        "api.trakt.tv/users/*/ratings/shows": "10s",
        "api.trakt.tv/users/*/ratings/movies": "10s",
        # Trakt search urls
        "api.trakt.tv/search/imdb/tt*?type=movie": "1d",
        "api.trakt.tv/search/imdb/tt*?type=show": "1d",
        "api.trakt.tv/search/imdb/tt*?type=episode": "1d",
        "api.trakt.tv/search/tmdb/*?type=movie": "1d",
        "api.trakt.tv/search/tmdb/*?type=show": "1d",
        "api.trakt.tv/search/tmdb/*?type=episode": "1d",
        "api.trakt.tv/search/tvdb/*?type=show": "1d",
        "api.trakt.tv/search/tvdb/*?type=episode": "1d",
        # Keep watched status cached, but fresh
        "api.trakt.tv/sync/watched/shows": "1s",
        "api.trakt.tv/users/*/watched/movies": "1s",
        # Watchlist better be fresh for next run
        "api.trakt.tv/users/*/watchlist/movies": "1s",
        "api.trakt.tv/users/*/watchlist/shows": "1s",
        "metadata.provider.plex.tv/library/sections/watchlist/all?*includeUserState=0": "60m",
        "metadata.provider.plex.tv/library/sections/watchlist/all": "10m",
        "api.trakt.tv/users/likes/lists": "5m",
        "api.trakt.tv/users/me": "60m",
        # Public Lists
        "api.trakt.tv/lists/*": "1d",
        # Online Plex patterns
        "metadata.provider.plex.tv/library/metadata/*/userState": DO_NOT_CACHE,
        "metadata.provider.plex.tv/library/metadata/*?*includeUserState=1": DO_NOT_CACHE,
        "metadata.provider.plex.tv/library/metadata/*": LONG_EXPIRY,
        "metadata.provider.plex.tv/library/search?query=*&searchTypes=movies&includeMetadata=1": "1h",
        "metadata.provider.plex.tv/library/search?query=*&searchTypes=tv&includeMetadata=1": "1h",
        # https://web.dev/stale-while-revalidate/
        # cache-control: max-age=0,stale-while-revalidate=86400
        "metadata.provider.plex.tv/": 86400,
        # Plex account
        # Cache for some time, this activates 304 responses
        "plex.tv/users/account": "1m",
        "plex.tv/api/v2/user": "15m",
        # plex-login command
        "plex.tv/api/v2/resources?includeHttps=1&includeRelay=1": "1m",
        # Plex patterns
        # Ratings search
        "*/library/sections/*/all?*userRating*=-1*": "10s",
        # len(PlexLibrarySection)
        "*/library/sections/*/all?*X-Plex-Container-Size=0": DO_NOT_CACHE,
        # __iter__(PlexLibrarySection)
        "*/library/sections/*/all?includeGuids=1": DO_NOT_CACHE,
        # find_by_title
        "*/library/sections/*/all?includeGuids=1&title=*": DO_NOT_CACHE,
        # episodes
        "*/library/sections/*/all?includeGuids=1&type=4*": DO_NOT_CACHE,
        # fetch_item, fetch_items
        "*/library/sections/*/all?*": DO_NOT_CACHE,
        "*/library/sections/*/collections?*X-Plex-Container-Size=0": DO_NOT_CACHE,
        "*/library/sections/*/collections": DO_NOT_CACHE,
        # library_sections
        "*/library/sections": DO_NOT_CACHE,
        # reloads
        "*/library/metadata/*?*include*": DO_NOT_CACHE,
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
        # Plex server root
        # version, updated_at
        "*/": "10m",
    }

    @property
    def urls_expire_after(self) -> ExpirationPatterns:
        """
        Create url patterns:
        - https://requests-cache.readthedocs.io/en/stable/examples.html#url-patterns
        - https://requests-cache.readthedocs.io/en/stable/user_guide/expiration.html#url-patterns

        NOTE: If there is more than one match, the first match will be used in the order they are defined
        """

        # We build dict from default_policy to keep the order of it
        policy = self.default_policy.copy()
        # This will keep the order if user overwrote the item
        policy.update(self.policy)

        for k, v in ((k, v) for k, v in policy.items() if isinstance(v, str)):
            # Special constants
            if v in self.expire_constants:
                policy[k] = self.expire_constants[v]
                continue
            # Parse string values with units to datetime
            policy[k] = parse_date(v)

        return policy

    def serialize(self):
        policy = self.urls_expire_after.copy()
        for k in (k for k, v in policy.items() if isinstance(v, timedelta)):
            policy[k] = str(policy[k])

        return {
            "http_cache": {
                "policy": policy,
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
