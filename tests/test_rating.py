#!/usr/bin/env python3 -m pytest
from datetime import datetime, timezone

from plextraktsync.util.Rating import Rating


def test_rating():
    r = Rating.create(None, datetime(2024, 1, 17, 2, 38, 49))
    assert r is None

    r = Rating.create(1.0, datetime(2024, 1, 17, 2, 38, 49))
    assert r.rating == 1
    assert r.rated_at == datetime(2024, 1, 17, 2, 38, 49)

    r = Rating.create(1.2, "2024-02-21T21:36:31.000Z")
    assert r.rating == 1
    assert r.rated_at == datetime(2024, 2, 21, 21, 36, 31, tzinfo=timezone.utc)
