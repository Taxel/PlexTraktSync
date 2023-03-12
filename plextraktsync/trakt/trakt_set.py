from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable

    from plextraktsync.trakt.types import TraktMedia


def trakt_set(collection: Iterable[TraktMedia]) -> set[int]:
    """
    Create set of trakt_id's from collection
    """
    return set(map(lambda m: m.trakt, collection))
