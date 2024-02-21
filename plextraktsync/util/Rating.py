from __future__ import annotations

from datetime import datetime
from typing import NamedTuple


class Rating(NamedTuple):
    rating: int
    rated_at: datetime
