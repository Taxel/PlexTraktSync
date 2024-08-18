from __future__ import annotations

import contextlib

from plexapi.exceptions import NotFound

from plextraktsync.config.ConfigLoader import ConfigLoader
from plextraktsync.decorators.coro import coro
from plextraktsync.factory import factory
from plextraktsync.plex.PlexApi import PlexApi
from plextraktsync.plex.PlexLibrarySection import PlexLibrarySection


def get_plex_from_name(name: str):
    try:
        server_name, library_name = name.split("/", 2)
    except ValueError:
        return None

    plex = factory.get_plex_by_name(server_name)
    if library_name.isnumeric():
        library = plex.library_sections[int(library_name)]
    else:
        library = [v for v in plex.library_sections.values() if v.title == library_name][0]
    return plex, library


def get_walker(plex: PlexApi, library: PlexLibrarySection):
    from plextraktsync.plan.WalkConfig import WalkConfig
    from plextraktsync.plan.Walker import Walker

    wc = WalkConfig()
    wc.add_library(library.title)

    return Walker(plex=plex, trakt=factory.trakt_api, mf=factory.media_factory, config=wc, progressbar=factory.progressbar)


async def load_movies(walker1, walker2):
    movies1 = set()
    async for pm in walker1.get_plex_movies():
        movies1.add(pm)

    movies2 = set()
    async for pm in walker2.get_plex_movies():
        movies2.add(pm)

    return movies1, movies2


def get_pairs(movies1, movies2):
    for pm1 in movies1:
        for pm2 in movies2:
            if pm1 == pm2:
                yield pm1, pm2


def cache_key(lib1: PlexLibrarySection, lib2: PlexLibrarySection):
    return "-".join(
        [
            str(p)
            for p in [
                lib1.section._server.machineIdentifier,
                lib1.section.key,
                lib2.section._server.machineIdentifier,
                lib2.section.key,
            ]
        ]
    )


@contextlib.contextmanager
def use_cache(cache_file: str):
    cache = dict()  # noqa
    with contextlib.suppress(FileNotFoundError):
        cache = ConfigLoader.load(cache_file)

    yield cache
    ConfigLoader.write(cache_file, cache)


@coro
async def compare_libraries(library1: str, library2: str, match_watched: bool):
    print = factory.print
    print(f"Compare contents of '{library1}' and '{library2}'")
    plex1, lib1 = get_plex_from_name(library1)
    plex2, lib2 = get_plex_from_name(library2)
    print(f"Loading contents of {lib1} and {lib2}")
    walker1 = get_walker(plex1, lib1)
    walker2 = get_walker(plex2, lib2)

    movies1, movies2 = await load_movies(walker1, walker2)
    matches = set()

    cache_file = f"compare-cache-{cache_key(lib1, lib2)}.json"
    with use_cache(cache_file) as cache:
        for pm1, pm2 in get_pairs(movies1, movies2):
            cached = cache.get(str(pm1.key))
            if cached:
                if not match_watched and cached != "not watched":
                    continue
            if match_watched and not pm1.is_watched:
                cache[str(pm1.key)] = "not watched"
                continue

            try:
                paths1 = set([part.file for part in pm1.parts])
                paths2 = set([part.file for part in pm2.parts])
            except NotFound as e:
                print(e)
                continue

            print(f"Checking match '{pm1.key}': {pm1.title_link} == {pm2.title_link}")
            print(paths1)
            print(paths2)
            matches.add(pm2)

    print(f"Made {len(matches)} matches")
