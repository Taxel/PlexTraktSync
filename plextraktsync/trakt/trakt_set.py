from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from plextraktsync.trakt.types import TraktMedia


def trakt_set(collection: Iterable[TraktMedia]) -> set[int]:
    """
    Create a set of trakt_id's from a collection
    """
    return set(map(lambda m: m.trakt, collection))
