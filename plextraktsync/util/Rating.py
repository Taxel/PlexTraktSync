from __future__ import annotations

from datetime import datetime
from typing import NamedTuple


class Rating(NamedTuple):
    rating: int
    rated_at: datetime

    def __eq__(self, other):
        """ Ratings are equal if their rating value is the same """
        return self.rating == other.rating
