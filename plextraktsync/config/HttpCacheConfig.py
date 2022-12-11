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

    @property
    def urls_expire_after(self) -> ExpirationPatterns:
        """
        Create url patterns:
        - https://requests-cache.readthedocs.io/en/stable/examples.html#url-patterns
        - https://requests-cache.readthedocs.io/en/stable/user_guide/expiration.html#url-patterns

        NOTE: If there is more than one match, the first match will be used in the order they are defined
        """
        return self.policy
