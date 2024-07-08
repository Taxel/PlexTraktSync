from __future__ import annotations

from plextraktsync.decorators.coro import coro
from plextraktsync.factory import factory


@coro
async def compare_libraries(library1: str, library2: str):
    print = factory.print
    print(f"Compare contents of '{library1}' and '{library2}'")
