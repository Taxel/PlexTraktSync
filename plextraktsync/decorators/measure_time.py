import logging
from contextlib import contextmanager
from time import time

from plextraktsync.factory import logger


@contextmanager
def measure_time(message, level=logging.INFO):
    start = time()
    yield
    timedelta = time() - start

    m, s = divmod(timedelta, 60)
    logger.log(
        level,
        f"{message} in " + (m > 0) * f"{m:.0f} min " + (s > 0) * f"{s:.1f} seconds",
    )
