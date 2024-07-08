from __future__ import annotations

from decorator import decorator

from plextraktsync.factory import factory

session = factory.session


@decorator
def nocache(method, *args, **kwargs):
    with session.cache_disabled():
        return method(*args, **kwargs)
