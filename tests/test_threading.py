#!/usr/bin/env python3 -m pytest
from time import sleep

from tests.conftest import factory


def test_threading():
    queue = factory.queue

    queue.add_to_collection(("movie", {"id": 1}))
    queue.add_to_collection(("movie", {"id": 2}))
    sleep(2)
    queue.remove_from_collection(("movie", {"id": 2}))
    sleep(3)
    queue.add_to_watchlist(("movie", {"id": 2}))
    sleep(4)
    queue.remove_from_watchlist(("movie", {"id": 2}))
    sleep(5)


if __name__ == "__main__":
    test_threading()
