from functools import wraps

from plex_trakt_sync.factory import factory

cache = factory.requests_cache()
session = factory.session()
config = factory.config()
trakt_cache = config["cache"]["path"]


def http_cache(method, expire_after=None):
    @wraps(method)
    def inner(self, *args, **kwargs):
        with cache.enabled(trakt_cache, expire_after=expire_after):
            with session.request_expire_after(expire_after):
                return method(self, *args, **kwargs)

    return inner
