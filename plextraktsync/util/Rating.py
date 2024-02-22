from __future__ import annotations

from datetime import datetime
from typing import NamedTuple


class Rating(NamedTuple):
    rating: int | float | None
    rated_at: datetime | str | None

    def __eq__(self, other):
        """ Ratings are equal if their rating value is the same """
        if self.rating is None or other.rating is None:
            return self.rating is other.rating

        return int(self.rating) == int(other.rating)

    @classmethod
    def create(cls, rating: int | float | None, rated_at: datetime | str | None):
        if rating is not None:
            rating = int(rating)
        if isinstance(rated_at, str):
            rated_at = datetime.fromisoformat(rated_at)

        return cls(rating, rated_at)
