import logging
from contextlib import contextmanager
from plex_trakt_sync.memoize import Memoize as memoize
from plex_trakt_sync.nocache import CacheDisabledDecorator as nocache
from time import time


@contextmanager
def measure_time(message, level=logging.INFO):
    start = time()
    yield
    timedelta = time() - start

    m, s = divmod(timedelta, 60)
    logging.log(level, message + " in " + (m > 0) * "{:.0f} min ".format(m) + (s > 0) * "{:.1f} seconds".format(s))
