from functools import wraps

import requests_cache


def nocache(method):
    @wraps(method)
    def inner(self, *args, **kwargs):
        with requests_cache.disabled():
            return method(self, *args, **kwargs)

    return inner
