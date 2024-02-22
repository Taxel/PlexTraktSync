from __future__ import annotations

from datetime import datetime, timezone
from typing import NamedTuple

from trakt.utils import timestamp


class Rating(NamedTuple):
    rating: int
    rated_at: datetime | None

    def __eq__(self, other):
        """ Ratings are equal if their rating value is the same """
        if isinstance(other, (int, float)):
            return self.rating == int(other)

        if other is None:
            return False

        return self.rating == other.rating

    def __str__(self):
        return f"Rating(rating={self.rating}, rated_at='{timestamp(self.rated_at)}')"

    @classmethod
    def create(cls, rating: int | float | None, rated_at: datetime | str | None):
        if rating is None:
            return None

        rating = int(rating)
        if isinstance(rated_at, str):
            try:
                rated_at = datetime.fromisoformat(rated_at)
            except ValueError:
                # Handle older Python < 3.11
                rated_at = (datetime.strptime(rated_at, "%Y-%m-%dT%H:%M:%S.%fZ")
                            # https://stackoverflow.com/questions/3305413/how-to-preserve-timezone-when-parsing-date-time-strings-with-strptime/63988322#63988322
                            .replace(tzinfo=timezone.utc))

        return cls(rating, rated_at)
