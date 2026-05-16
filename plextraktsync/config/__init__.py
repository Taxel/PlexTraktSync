"""
Platform name to identify our application
"""

from __future__ import annotations

PLEX_PLATFORM = "PlexTraktSync"

"""
Constant in seconds for how much to wait between Trakt POST API calls.
POST requests are limited to 1 call/second per user.
"""
TRAKT_POST_DELAY = 1.1

"""
Constant in seconds for how much to wait between Trakt GET API calls.
GET requests are limited to 1,000 calls per 5 minutes (~0.3s between calls).
"""
TRAKT_GET_DELAY = 0.3

"""
Constants in seconds for the margin added to retry-after delay to account for network jitter in rate limiting retries.
"""
TRAKT_RETRY_AFTER_MARGIN = 0.9
