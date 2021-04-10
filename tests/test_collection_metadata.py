#!/usr/bin/env python3 -m pytest
import pytest
from datetime import datetime
from plex_trakt_sync.plex_api import PlexLibraryItem
from tests.conftest import make

testdata = [
    (
        make(
            addedAt=datetime(1999, 1, 1),
            media=[
                make(
                    videoResolution="720",
                    audioChannels=2,
                ),
            ],
        ),
        {
            'collected_at': '1998-12-31:T22:00:00.000Z',
            'media_type': 'digital',
            'resolution': 'hd_720p',
            'audio_channels': '2.0',
        }
    ),
]


@pytest.mark.parametrize("test_input,expected", testdata)
def test_collection_metadata(test_input, expected):
    m = PlexLibraryItem(test_input)
    json = m.to_json()

    assert expected == json, f"Unexpected! {json}"
