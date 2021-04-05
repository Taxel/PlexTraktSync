import logging
from contextlib import contextmanager
from time import time


@contextmanager
def measure_time(message, level=logging.INFO):
    start = time()
    yield
    timedelta = time() - start

    m, s = divmod(timedelta, 60)
    logging.log(level, message + " in " + (m > 0) * "{:.0f} min ".format(m) + (s > 0) * "{:.1f} seconds".format(s))
