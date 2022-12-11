from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict

    from requests_cache import ExpirationPatterns


@dataclass(frozen=True)
class HttpCacheConfig:
    """
    Main config dataclass
    """

    policy: Dict[str]

    default_policy = {
        # Requests matching these patterns will not be cached
        "*.trakt.tv/shows/*/seasons": 0,
        "*.trakt.tv/sync/collection/shows": 0,
        "*.trakt.tv/sync/watched/shows": 0,
        "*.trakt.tv/users/*/collection/movies": 0,
        "*.trakt.tv/users/*/collection/shows": 0,
        "*.trakt.tv/users/*/ratings/*": 0,
        "*.trakt.tv/users/*/watched/movies": 0,
        "*.trakt.tv/users/*/watchlist/movies": 0,
        "*.trakt.tv/users/*/watchlist/shows": 0,
        "*.trakt.tv/users/likes/lists": 0,
        "*.trakt.tv/users/me": 0,
    }

    @property
    def urls_expire_after(self) -> ExpirationPatterns:
        """
        Create url patterns:
        - https://requests-cache.readthedocs.io/en/stable/examples.html#url-patterns
        - https://requests-cache.readthedocs.io/en/stable/user_guide/expiration.html#url-patterns

        NOTE: If there is more than one match, the first match will be used in the order they are defined
        """

        policy = dict(self.default_policy)
        if self.policy:
            policy.update(self.policy)

        return policy
