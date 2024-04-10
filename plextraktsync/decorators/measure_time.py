from contextlib import contextmanager
from datetime import timedelta
from time import monotonic

from humanize.time import precisedelta

from plextraktsync.factory import logging

logger = logging.getLogger(__name__)


@contextmanager
def measure_time(message, level=logging.INFO, **kwargs):
    start = monotonic()
    yield
    delta = monotonic() - start

    minimum_unit = "microseconds" if delta < 1 else "seconds"
    logger.log(
        level,
        f"{message} in " + precisedelta(timedelta(seconds=delta), minimum_unit=minimum_unit),
        **kwargs
    )
