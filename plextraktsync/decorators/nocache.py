from functools import wraps

from plextraktsync.factory import factory

session = factory.session


def nocache(method):
    @wraps(method)
    def inner(*args, **kwargs):
        with session.cache_disabled():
            return method(*args, **kwargs)

    return inner
