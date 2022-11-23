from functools import wraps

from requests_cache import CachedSession, ExpirationTime

from plextraktsync.factory import factory

session: CachedSession = factory.session


def http_cache(expire_after: ExpirationTime = None):
    def decorator(fn):
        @wraps(fn)
        def inner(self, *args, **kwargs):
            previous = session.expire_after
            session.expire_after = expire_after
            try:
                return fn(self, *args, **kwargs)
            finally:
                session.expire_after = previous

        return inner

    return decorator
