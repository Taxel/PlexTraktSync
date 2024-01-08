#!/usr/bin/env python3 -m pytest
import asyncio

import pytest

from plextraktsync.sync import Sync
from plextraktsync.walker import Walker
from tests.conftest import factory


async def items(max_items: int):
    for item in range(max_items):
        yield item


async def test_async_generator():
    async for item in items(3):
        print(item)
    # print(c)


@pytest.mark.asyncio
async def test_plex_sync():
    walker: Walker = factory.walker
    runner: Sync = factory.sync
    await runner.sync(walker, dry_run=True)


if __name__ == '__main__':
    asyncio.run(test_plex_sync())
    # asyncio.run(test_async_generator())
