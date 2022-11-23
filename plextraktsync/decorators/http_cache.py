from functools import wraps

from requests_cache import CachedSession

from plextraktsync.factory import factory

session: CachedSession = factory.session


def http_cache(method, expire_after=None):
    @wraps(method)
    def inner(self, *args, **kwargs):
        with session.request_expire_after(expire_after):
            return method(self, *args, **kwargs)

    return inner
