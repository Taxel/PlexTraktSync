from __future__ import annotations

import re
from functools import cached_property


class PlexAudioCodec:
    def match(self, codec):
        for key, regex in self.audio_codecs.items():
            if key == codec:
                return key

            if regex and regex.match(codec):
                return key

        return None

    @cached_property
    def audio_codecs(self):
        codecs = {
            "lpcm": "pcm",
            "mp3": None,
            "aac": None,
            "ogg": "vorbis",
            "wma": None,
            "dts": "(dca|dta)",
            "dts_ma": "dtsma",
            "dolby_prologic": "dolby.?pro",
            "dolby_digital": "ac.?3",
            "dolby_digital_plus": "eac.?3",
            "dolby_truehd": "truehd",
        }

        # compile patterns
        for k, v in codecs.items():
            if v is None:
                continue

            try:
                codecs[k] = re.compile(v, re.IGNORECASE)
            except Exception:
                raise RuntimeError("Unable to compile regex pattern: %r", v, exc_info=True)
        return codecs
