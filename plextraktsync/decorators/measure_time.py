import inspect
from contextlib import contextmanager
from datetime import timedelta
from time import monotonic

from humanize.time import precisedelta

from plextraktsync.factory import logging

default_logger = logging.getLogger(__name__)


@contextmanager
def measure_time(message, *args, level=logging.INFO, logger=None, **kwargs):
    start = monotonic()
    yield
    delta = monotonic() - start

    if inspect.ismethod(logger):
        log = logger
    else:
        def log(*a, **kw):
            (logger or default_logger).log(level, *a, **kw)

    minimum_unit = "microseconds" if delta < 1 else "seconds"
    log(
        f"{message} in %s",
        precisedelta(timedelta(seconds=delta), minimum_unit=minimum_unit),
        *args,
        **kwargs,
    )
