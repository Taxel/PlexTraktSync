#!/usr/bin/env python3 -m pytest
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from plextraktsync.sync.SyncRatingsPlugin import SyncRatingsPlugin
from plextraktsync.util.Rating import Rating


class Config(dict):
    def __init__(self, rating_priority="newer_wins", plex_to_trakt=True, trakt_to_plex=True):
        super().__init__({"rating_priority": rating_priority})
        self.plex_to_trakt = {"ratings": plex_to_trakt}
        self.trakt_to_plex = {"ratings": trakt_to_plex}


class Media(SimpleNamespace):
    title_link = "Test Movie"

    def __init__(self, plex_rating=None, trakt_rating=None):
        super().__init__(
            plex_rating=plex_rating,
            trakt_rating=trakt_rating,
            plex_rate_calls=0,
            trakt_rate_calls=0,
        )

    def plex_rate(self):
        self.plex_rate_calls += 1

    def trakt_rate(self):
        self.trakt_rate_calls += 1


UTC = timezone.utc
OLDER = datetime(2024, 1, 1, tzinfo=UTC)
NEWER = datetime(2024, 2, 1, tzinfo=UTC)


async def sync(media, *, dry_run=False, plex_to_trakt=True, trakt_to_plex=True):
    plugin = SyncRatingsPlugin(Config(plex_to_trakt=plex_to_trakt, trakt_to_plex=trakt_to_plex))
    await plugin.sync_ratings(media, dry_run=dry_run)
    return media


@pytest.mark.asyncio
async def test_newer_wins_rates_trakt_when_plex_rating_is_newer():
    media = Media(
        plex_rating=Rating(9, NEWER),
        trakt_rating=Rating(8, OLDER),
    )

    await sync(media)

    assert media.trakt_rate_calls == 1
    assert media.plex_rate_calls == 0


@pytest.mark.asyncio
async def test_newer_wins_rates_plex_when_trakt_rating_is_newer():
    media = Media(
        plex_rating=Rating(9, OLDER),
        trakt_rating=Rating(8, NEWER),
    )

    await sync(media)

    assert media.plex_rate_calls == 1
    assert media.trakt_rate_calls == 0


@pytest.mark.asyncio
async def test_newer_wins_fills_missing_trakt_rating_from_plex():
    media = Media(plex_rating=Rating(9, NEWER), trakt_rating=None)

    await sync(media)

    assert media.trakt_rate_calls == 1
    assert media.plex_rate_calls == 0


@pytest.mark.asyncio
async def test_newer_wins_fills_missing_plex_rating_from_trakt():
    media = Media(plex_rating=None, trakt_rating=Rating(8, NEWER))

    await sync(media)

    assert media.plex_rate_calls == 1
    assert media.trakt_rate_calls == 0


@pytest.mark.asyncio
async def test_newer_wins_does_not_rate_when_values_match():
    media = Media(
        plex_rating=Rating(8, OLDER),
        trakt_rating=Rating(8, NEWER),
    )

    await sync(media)

    assert media.plex_rate_calls == 0
    assert media.trakt_rate_calls == 0


@pytest.mark.asyncio
async def test_newer_wins_respects_disabled_plex_to_trakt_direction():
    media = Media(
        plex_rating=Rating(9, NEWER),
        trakt_rating=Rating(8, OLDER),
    )

    await sync(media, plex_to_trakt=False)

    assert media.trakt_rate_calls == 0
    assert media.plex_rate_calls == 0


@pytest.mark.asyncio
async def test_newer_wins_respects_disabled_trakt_to_plex_direction():
    media = Media(
        plex_rating=Rating(9, OLDER),
        trakt_rating=Rating(8, NEWER),
    )

    await sync(media, trakt_to_plex=False)

    assert media.plex_rate_calls == 0
    assert media.trakt_rate_calls == 0


@pytest.mark.asyncio
async def test_newer_wins_uses_plex_when_timestamps_are_missing():
    media = Media(
        plex_rating=Rating(9, None),
        trakt_rating=Rating(8, None),
    )

    await sync(media)

    assert media.trakt_rate_calls == 1
    assert media.plex_rate_calls == 0


@pytest.mark.asyncio
async def test_newer_wins_dry_run_does_not_write():
    media = Media(
        plex_rating=Rating(9, NEWER),
        trakt_rating=Rating(8, OLDER),
    )

    await sync(media, dry_run=True)

    assert media.trakt_rate_calls == 0
    assert media.plex_rate_calls == 0
