#!/usr/bin/env python3 -m pytest
import asyncio

import pytest

from plextraktsync.sync import Sync
from plextraktsync.walker import Walker
from tests.conftest import factory


@pytest.mark.asyncio
async def test_plex_sync():
    walker: Walker = factory.walker
    runner: Sync = factory.sync
    await runner.sync(walker, dry_run=True)


if __name__ == '__main__':
    asyncio.run(test_plex_sync())
