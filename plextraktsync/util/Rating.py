from __future__ import annotations

from datetime import datetime
from typing import NamedTuple


class Rating(NamedTuple):
    rating: int
    rated_at: datetime

    def __eq__(self, other):
        """ Ratings are equal if their rating value is the same """
        if self.rating is None or other.rating is None:
            return self.rating is other.rating

        return int(self.rating) == int(other.rating)
