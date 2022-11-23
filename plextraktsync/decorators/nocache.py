from functools import wraps

from requests_cache import CachedSession

from plextraktsync.factory import factory

session: CachedSession = factory.session


def nocache(method):
    @wraps(method)
    def inner(*args, **kwargs):
        with session.cache_disabled():
            return method(*args, **kwargs)

    return inner
