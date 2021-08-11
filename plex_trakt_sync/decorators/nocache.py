from functools import wraps

from plex_trakt_sync.factory import factory

cache = factory.requests_cache()
session = factory.session()


def nocache(method):
    @wraps(method)
    def inner(*args, **kwargs):
        with cache.disabled():
            with session.cache_disabled():
                return method(*args, **kwargs)

    return inner
