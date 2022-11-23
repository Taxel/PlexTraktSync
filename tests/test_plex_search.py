#!/usr/bin/env python3 -m pytest
from tests.conftest import factory

plex = factory.plex_api


def test_plex_search():
    search = plex.search("The Addams Family (1964)", libtype="show")
    results = [m for m in search]

    assert len(results) == 1

    m = results[0]
    guid = m.guids[0]

    assert m.type == "show"
    assert m.item.title == "The Addams Family (1964)"
    assert guid.provider == "tvdb"
    assert guid.id == "77137"
