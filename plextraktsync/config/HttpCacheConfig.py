from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from requests_cache import DO_NOT_CACHE

if TYPE_CHECKING:
    from requests_cache import ExpirationPatterns


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

    def dump(self, print=None):
        """
        Print config serialized as yaml.
        If print is None, return the produced string instead.
        """
        from plextraktsync.config.ConfigLoader import ConfigLoader
        data = {
            "http_cache": {
                "policy": self.urls_expire_after,
            },
        }
        dump = ConfigLoader.dump_yaml(None, data)
        if print is None:
            return dump
        print(dump)
