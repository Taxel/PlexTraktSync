from functools import wraps

from plextraktsync.factory import factory

session = factory.session()


def http_cache(method, expire_after=None):
    @wraps(method)
    def inner(self, *args, **kwargs):
        with session.request_expire_after(expire_after):
            return method(self, *args, **kwargs)

    return inner
