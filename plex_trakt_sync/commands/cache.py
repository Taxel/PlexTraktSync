from functools import partial

import click
from requests_cache import CachedSession

from plex_trakt_sync.path import trakt_cache


def get_sorted_cache(session: CachedSession, sorting: str, reverse: bool):
    get_responses = getattr(session.cache, "values", None)
    if not callable(get_responses):
        raise RuntimeError("This command requires requests_cache 0.7.x")

    sorters = {
        "size": lambda r: r.size,
        "date": lambda r: r.created_at,
        "url": lambda r: r.url,
    }
    sorter = partial(sorted, reverse=reverse, key=sorters[sorting])

    yield from sorter(get_responses())


# https://stackoverflow.com/questions/36106712/how-can-i-limit-iterations-of-a-loop-in-python
def limit_iterator(items, limit: int):
    if not limit or limit <= 0:
        i = 0
        for v in items:
            yield i, v
            i += 1

    else:
        yield from zip(range(limit), items)


@click.command()
@click.option(
    "--sort",
    type=click.Choice(["size", "date", "url"], case_sensitive=False),
    default="size",
    show_default=True, help="Sort mode"
)
@click.option(
    "--limit",
    type=int,
    default=20,
    show_default=True, help="Limit entries to be printed"
)
@click.option(
    "--reverse",
    is_flag=True,
    default=False,
    help="Sort reverse"
)
def cache(sort: str, limit: int, reverse: bool):
    """
    Manage and analyze Requests Cache.
    """
    session = CachedSession(cache_name=trakt_cache, backend='sqlite')
    click.echo(f"Cache status:\n{session.cache}\n")

    click.echo("URLs:")
    sorted = get_sorted_cache(session, sort, reverse)
    for i, r in limit_iterator(sorted, limit):
        click.echo(f"- {i + 1:3d}. {r}")
