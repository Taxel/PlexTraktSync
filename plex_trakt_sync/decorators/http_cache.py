from functools import wraps

import requests_cache

from plex_trakt_sync.path import trakt_cache


def http_cache(method, expire_after=None):
    @wraps(method)
    def inner(self, *args, **kwargs):
        with requests_cache.enabled(trakt_cache, expire_after=expire_after):
            return method(self, *args, **kwargs)

    return inner
