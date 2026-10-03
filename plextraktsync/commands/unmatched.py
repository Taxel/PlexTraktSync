from __future__ import annotations

from plextraktsync.commands.login import ensure_login
from plextraktsync.decorators.coro import coro
from plextraktsync.factory import factory


def select_libraries(walker, library: tuple[str, ...]):
    """
    Add requested libraries to walk config and ensure they are movie libraries.
    """

    if not library:
        return

    for name in library:
        walker.config.add_library(name)

    if walker.plan.show_sections:
        titles = ", ".join(f"'{s.title}'" for s in walker.plan.show_sections)
        raise RuntimeError(f"Library {titles} is not a movie library, only movie libraries can be scanned")


@coro
async def unmatched(no_progress_bar: bool, local: bool, library: tuple[str, ...]):
    factory.run_config.update(progressbar=not no_progress_bar)
    ensure_login()
    plex = factory.plex_api
    mf = factory.media_factory
    wc = factory.walk_config
    walker = factory.walker

    select_libraries(walker, library)

    if not wc.is_valid:
        print("Nothing to scan, this is likely due conflicting options given.")
        return

    failed = []
    if local:
        async for pm in walker.get_plex_movies():
            if all(guid.local for guid in pm.guids):
                failed.append(pm)
    else:
        async for pm in walker.get_plex_movies():
            movie = mf.resolve_any(pm)
            if not movie:
                failed.append(pm)

    for i, pm in enumerate(failed):
        p = pm.item
        url = plex.media_url(pm)
        print("=", i, "=" * 80)
        print(f"No match: {pm}")
        print(f"URL: {url}")
        print(f"Title: {p.title}")
        print(f"Year: {p.year}")
        print(f"Updated At: {p.updatedAt}")
        for location in p.locations:
            print(f"Location: {location}")

        print("")
