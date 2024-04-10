from contextlib import contextmanager
from time import monotonic

from plextraktsync.factory import logging

logger = logging.getLogger(__name__)


@contextmanager
def measure_time(message, level=logging.INFO, **kwargs):
    start = monotonic()
    yield
    timedelta = monotonic() - start

    m, s = divmod(timedelta, 60)
    logger.log(
        level,
        f"{message} in " + (m > 0) * f"{m:.0f} min " + (s > 0) * f"{s:.1f} seconds",
        **kwargs
    )
