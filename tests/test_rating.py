#!/usr/bin/env python3 -m pytest
from datetime import datetime

from plextraktsync.util.Rating import Rating


def test_rating():
    r = Rating.create(None, datetime(2024, 1, 17, 2, 38, 49))
    assert r is None

    r = Rating.create(1.0, datetime(2024, 1, 17, 2, 38, 49))
    assert r.rating == 1
    assert r.rated_at == datetime(2024, 1, 17, 2, 38, 49)
