from functools import wraps

from plextraktsync.factory import factory


def nocache(method):
    @wraps(method)
    def inner(*args, **kwargs):
        session = factory.session()
        with session.cache_disabled():
            return method(*args, **kwargs)

    return inner
