from __future__ import annotations

from decorator import decorator

from plextraktsync.config import TRAKT_GET_DELAY
from plextraktsync.util.Timer import Timer

timer = Timer(TRAKT_GET_DELAY)


@decorator
def get_limit(fn, *args, **kwargs):
    """
    Throttles GET calls not to exceed Trakt's GET rate limit (1,000 per 5 minutes).
    Uses a separate timer from time_limit to avoid conflating GET and POST budgets.
    """

    timer.wait_if_needed()

    return fn(*args, **kwargs)
