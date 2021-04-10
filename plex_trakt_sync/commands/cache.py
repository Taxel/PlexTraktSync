import click
from requests_cache import CachedSession

from plex_trakt_sync.path import trakt_cache


@click.command()
def cache():
    """
    Manage and analyze Requests Cache.
    """
    session = CachedSession(cache_name=trakt_cache, backend='sqlite')
    click.echo(f"Cache status:\n{session.cache}\n")

    click.echo(f"URLs:")
    for url in session.cache.urls:
        click.echo(f"- {url}")
