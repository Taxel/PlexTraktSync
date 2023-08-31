#!/usr/bin/env python3 -m pytest
from plextraktsync.plex.PlexId import PlexId
from plextraktsync.plex.PlexIdFactory import PlexIdFactory

# sha1 of "PlexTraktSync"
SERVER_ID = "2ac365831928c7ad926484eae3c65e3a88112c54"


def test_plex_id_numeric():
    pid = PlexIdFactory.create(10)
    assert pid.key == 10
    assert pid.media_type is None
    assert pid.provider is None
    assert pid.server is None
    assert pid.is_discover is False

    pid = PlexIdFactory.create("10")
    assert pid.key == 10
    assert pid.media_type is None
    assert pid.provider is None
    assert pid.server is None
    assert pid.is_discover is False


def test_plex_id_urls():
    pid = PlexIdFactory.create(
        f"https://app.plex.tv/desktop/#!/server/{SERVER_ID}/details?key=%2Flibrary%2Fmetadata%2F13202"
    )
    assert pid.key == 13202
    assert pid.media_type is None
    assert pid.provider is None
    assert pid.server == SERVER_ID
    assert pid.is_discover is False

    pid = PlexIdFactory.create(
        f"https://app.plex.tv/desktop/#!/server/{SERVER_ID}/playHistory?filters=metadataItemID%3D6041&filterTitle=&isParentType=false"
    )
    assert pid.key == 6041
    assert pid.media_type is None
    assert pid.provider is None
    assert pid.server == SERVER_ID
    assert pid.is_discover is False


def test_plex_id_discover_url():
    pid = PlexIdFactory.create(
        "https://app.plex.tv/desktop/#!/provider/tv.plex.provider.discover/details?key=%2Flibrary%2Fmetadata%2F5d7768532e80df001ebe18e7"
    )
    assert pid.key == "5d7768532e80df001ebe18e7"
    assert pid.media_type is None
    assert pid.provider == PlexId.METADATA
    assert pid.server is None
    assert pid.is_discover is True


def test_plex_id_discover_url2():
    pid = PlexIdFactory.create(
        "https://app.plex.tv/desktop/#!/provider/tv.plex.provider.discover/details?key=/library/metadata/5d776a8e51dd69001fe24eb8"
    )
    assert pid.key == "5d776a8e51dd69001fe24eb8"
    assert pid.media_type is None
    assert pid.provider == PlexId.METADATA
    assert pid.server is None
    assert pid.is_discover is True
