from functools import partial

import click
from requests_cache import CachedSession

from plex_trakt_sync.path import trakt_cache


def get_sorted_cache(session: CachedSession, sorting: str):
    sorters = {
        "size": partial(sorted, reverse=True, key=lambda x: len(x[1].content)),
        "date": partial(sorted, reverse=True, key=lambda x: x[1].created_at),
    }
    sorter = sorters[sorting]
    yield from sorter(session.cache._get_valid_responses())


@click.command()
@click.option(
    "--sort",
    type=click.Choice(["size", "date"], case_sensitive=False),
    default="size",
    show_default=True, help="Sort mode"
)
def cache(sort: str):
    """
    Manage and analyze Requests Cache.
    """
    session = CachedSession(cache_name=trakt_cache, backend='sqlite')
    click.echo(f"Cache status:\n{session.cache}\n")

    click.echo(f"URLs:")
    for k, r in get_sorted_cache(session, sort):
        click.echo(f"- {r.created_at}: {r.url}: {len(r.content)} bytes")
