#!/usr/bin/env python3 -m pytest
from contextlib import contextmanager
from time import perf_counter, sleep

from plextraktsync.util.Timer import Timer


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


def test_timer_remaining():
    time_limit = 1.1
    timer = Timer(time_limit)
    timer.start()

    loops = 0
    with timeit() as t:
        print(f"remaining: {timer.time_remaining}")
        timer.update()
        while timer.time_remaining > 0.0:
            print(f"remaining: {timer.time_remaining}")
            sleep(0.1)
            loops += 1
    assert t() >= time_limit
    assert loops > 0
