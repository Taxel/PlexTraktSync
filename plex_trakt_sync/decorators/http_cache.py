from functools import wraps

from plex_trakt_sync.factory import factory
from plex_trakt_sync.path import trakt_cache

cache = factory.requests_cache()


def http_cache(method, expire_after=None):
    @wraps(method)
    def inner(self, *args, **kwargs):
        with cache.enabled(trakt_cache, expire_after=expire_after):
            return method(self, *args, **kwargs)

    return inner
