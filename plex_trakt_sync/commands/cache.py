from functools import partial

import click
from requests_cache import CachedSession

from plex_trakt_sync.path import trakt_cache


def get_sorted_cache(session: CachedSession, sorting: str, reverse: bool):
    get_valid_responses = getattr(session.cache, "_get_valid_responses", None)
    if not callable(get_valid_responses):
        raise RuntimeError(f"This command requires requests_cache 0.6.x")

    sorters = {
        "size": partial(sorted, reverse=reverse, key=lambda x: len(x[1].content)),
        "date": partial(sorted, reverse=reverse, key=lambda x: x[1].created_at),
        "url": partial(sorted, reverse=reverse, key=lambda x: x[1].url),
    }
    sorter = sorters[sorting]
    yield from sorter(get_valid_responses())


# https://stackoverflow.com/questions/36106712/how-can-i-limit-iterations-of-a-loop-in-python
def limit_iterator(items, limit: int):
    if not limit or limit <= 0:
        i = 0
        for k, v in items:
            yield i, (k, v)
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

    click.echo(f"URLs:")
    sorted = get_sorted_cache(session, sort, reverse)
    for i, (k, r) in limit_iterator(sorted, limit):
        click.echo(f"- {i + 1:3d}. {r.created_at}: {r.url}: {len(r.content)} bytes")
