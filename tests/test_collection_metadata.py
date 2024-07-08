#!/usr/bin/env python3 -m pytest
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
from tests.conftest import make

testdata = [
    (
        make(
            addedAt=datetime(1999, 1, 1, tzinfo=timezone.utc),
            media=[
                make(
                    width=1280,
                    audioChannels=2,
                ),
            ],
        ),
        {
            "collected_at": "1999-01-01:T00:00:00.000Z",
            "media_type": "digital",
            "resolution": "hd_720p",
            "audio_channels": "2.0",
        },
    ),
    (
        make(
            addedAt=datetime(1999, 1, 1, tzinfo=timezone.utc),
            media=[
                make(
                    width=1280,
                    audioChannels=2,
                    parts=make(
                        streams=[
                            make(
                                streamType="1",
                                codec="hevc",
                                displayTitle="4K (HEVC Main 10)",
                            ),
                            make(
                                streamType="2",
                                channels="6",
                                audioChannelLayout="5.1(side)",
                                displayTitle="English (EAC3 5.1)",
                            ),
                        ]
                    ),
                ),
            ],
        ),
        {
            "collected_at": "1999-01-01:T00:00:00.000Z",
            "media_type": "digital",
            "resolution": "hd_720p",
            "audio_channels": "2.0",
        },
    ),
]


@pytest.mark.parametrize("test_input,expected", testdata)
@pytest.mark.skip(reason="Broken in CI")
def test_collection_metadata(test_input, expected):
    m = PlexLibraryItem(test_input)
    json = m.to_json()

    assert expected == json, f"Unexpected! {json}"
