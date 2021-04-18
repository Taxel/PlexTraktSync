#!/usr/bin/env python3 -m pytest
from contextlib import contextmanager
from time import perf_counter

from plex_trakt_sync.timer import Timer


@contextmanager
def timeit():
    # https://stackoverflow.com/a/62956469/2314626
    start = perf_counter()
    yield lambda: perf_counter() - start


def test_timer():
    time_limit = 1.1
    timer = Timer(time_limit)

    with timeit() as t:
        timer.wait_if_needed()
    assert t() < time_limit, "First call is free!"

    with timeit() as t:
        timer.wait_if_needed()
    assert t() > time_limit, "Second call must have waited"

    with timeit() as t:
        timer.wait_if_needed()
        timer.wait_if_needed()
        timer.wait_if_needed()
    assert t() > 3 * time_limit, "Wait three times"
