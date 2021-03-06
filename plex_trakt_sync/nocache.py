import requests_cache


class CacheDisabledDecorator:
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *args):
        with requests_cache.disabled():
            return self.fn(*args)
