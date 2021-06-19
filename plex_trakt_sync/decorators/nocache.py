from functools import wraps

from plex_trakt_sync.factory import factory

cache = factory.requests_cache()


def nocache(method):
    @wraps(method)
    def inner(self, *args, **kwargs):
        with cache.disabled():
            return method(self, *args, **kwargs)

    return inner
