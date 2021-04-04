import logging
from contextlib import contextmanager
from time import time
from plex_trakt_sync.nocache import CacheDisabledDecorator as nocache

try:
    from functools import cache as memoize
except ImportError:
    # For py<3.9
    # https://docs.python.org/3.9/library/functools.html
    from functools import lru_cache as memoize


@contextmanager
def measure_time(message, level=logging.INFO):
    start = time()
    yield
    timedelta = time() - start

    m, s = divmod(timedelta, 60)
    logging.log(level, message + " in " + (m > 0) * "{:.0f} min ".format(m) + (s > 0) * "{:.1f} seconds".format(s))
