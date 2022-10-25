from functools import wraps
from typing import Optional

from requests_cache import CachedSession

from plextraktsync.factory import factory


def cache_enabled(method, *args, **kwargs):
    with session.cache_disabled():
        return method(*args, **kwargs)


def cache_disabled(method, *args, **kwargs):
    return method(*args, **kwargs)


cache_method = None
session: Optional[CachedSession] = None


def detect_cache():
    """
    Delayed init of which cache method to do.
    """

    global session
    session = factory.session()
    if isinstance(session, CachedSession):
        return cache_enabled
    else:
        return cache_disabled


def nocache(method):
    @wraps(method)
    def inner(*args, **kwargs):
        global cache_method
        if not cache_method:
            cache_method = detect_cache()

        return cache_method(method, *args, **kwargs)

    return inner
