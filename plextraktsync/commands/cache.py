from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from plextraktsync.factory import factory

if TYPE_CHECKING:
    from typing import Any, Generator

    from requests_cache import CachedRequest, CachedSession


def get_sorted_cache(session: CachedSession, sorting: str, reverse: bool):
    sorters = {
        "size": lambda r: r.size,
        "date": lambda r: r.created_at,
        "url": lambda r: r.url,
    }
    sorter = partial(sorted, reverse=reverse, key=sorters[sorting])

    yield from sorter(session.cache.responses.values())


def responses_by_url(
    session: CachedSession, url: str
) -> Generator[CachedRequest, Any, None]:
    return (
        response for response in session.cache.responses.values() if response.url == url
    )


# https://stackoverflow.com/questions/36106712/how-can-i-limit-iterations-of-a-loop-in-python
def limit_iterator(items, limit: int):
    if not limit or limit <= 0:
        i = 0
        for v in items:
            yield i, v
            i += 1

    else:
        yield from zip(range(limit), items)


def render_xml(data):
    from xml.etree import ElementTree

    if not data.strip():
        return None

    root = ElementTree.fromstring(data)
    try:
        # requires python 3.9
        # https://stackoverflow.com/a/39482716/2314626
        ElementTree.indent(root)
    except AttributeError:
        pass

    return ElementTree.tostring(root, encoding="utf8").decode("utf8")


def render_json(data):
    from json import dumps, loads

    decoded = loads(data)
    return dumps(decoded, indent=2)


def expire_url(session: CachedSession, url: str):
    print(f"Expiring: {url}")
    session.cache.delete(urls=[url])


def inspect_url(session: CachedSession, url: str):
    matches = responses_by_url(session, url)
    for m in matches:
        content_type = m.headers["Content-Type"]
        if content_type.startswith("text/xml") or content_type.startswith(
            "application/xml"
        ):
            print(f"<!-- {m} -->")
            for name, value in m.headers.items():
                print(f"<!-- {name}: {value} -->")
            print(render_xml(m.content))
        elif content_type.startswith("application/json"):
            print(f"// {m}")
            for name, value in m.headers.items():
                print(f"// {name}: {value}")
            print(render_json(m.content))
        else:
            print(f"# {content_type}: {m.url}")
            for name, value in m.headers.items():
                print(f"# {name}: {value}")
            print(m.content)


def cache_status(cache):
    # https://github.com/requests-cache/requests-cache/commit/35b48cf3486e546a5e4090e8e410b698e8a6b7be#r87356998
    return f"Total rows: {len(cache.responses)} responses, {len(cache.redirects)} redirects"


def cache(sort: str, limit: int, reverse: bool, expire: bool, url: str):
    session = factory.session
    print = factory.print

    if expire:
        expire_url(session, url)
        return

    if url:
        inspect_url(session, url)
        return

    print(f"Cache status:\n{cache_status(session.cache)}\n")

    print("URLs:")
    sorted = get_sorted_cache(session, sort, reverse)
    for i, r in limit_iterator(sorted, limit):
        print(f"- {i + 1:3d}. {r}", crop=False, overflow="ignore")
