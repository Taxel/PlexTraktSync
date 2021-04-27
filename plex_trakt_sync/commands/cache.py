from functools import partial

import click
from requests_cache import CachedSession

from plex_trakt_sync.path import trakt_cache


def get_sorted_cache(session: CachedSession):
    sorter = partial(sorted, reverse=True, key=lambda x: len(x[1].content))
    yield from sorter(session.cache._get_valid_responses())


@click.command()
def cache():
    """
    Manage and analyze Requests Cache.
    """
    session = CachedSession(cache_name=trakt_cache, backend='sqlite')
    click.echo(f"Cache status:\n{session.cache}\n")

    click.echo(f"URLs:")
    for k, r in get_sorted_cache(session):
        click.echo(f"- {r.created_at}: {r.url}: {len(r.content)} bytes")
