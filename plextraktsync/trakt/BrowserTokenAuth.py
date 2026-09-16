"""Opt-in authentication using credentials supplied by the user's browser."""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from urllib.parse import urlsplit

from click import ClickException
from requests.auth import AuthBase


class BrowserTokenAuth(AuthBase):
    def __init__(self, path):
        self.path = Path(path)

    def read(self):
        try:
            data = json.loads(self.path.read_text())
            if not isinstance(data, dict):
                raise ValueError()
            for key in ("access_token", "client_id"):
                value = data.get(key)
                if not isinstance(value, str) or not value or any(c.isspace() for c in value):
                    raise ValueError()
            expires = data.get("expires_at")
            if expires is not None:
                if isinstance(expires, bool) or not isinstance(expires, (int, float)) or not math.isfinite(expires):
                    raise ValueError()
                if expires <= time.time():
                    raise ClickException("Trakt browser token expired. Update the browser token file.")
            return data
        except (OSError, ValueError):
            raise ClickException("Cannot read Trakt browser token file: expected access_token, client_id and optional numeric expires_at.") from None

    def __call__(self, request):
        url = urlsplit(request.url)
        if url.scheme != "https" or url.netloc != "api.trakt.tv":
            raise ClickException("Refusing to send Trakt browser credentials to an unexpected endpoint.")
        data = self.read()
        request.headers["Authorization"] = "Bearer " + data["access_token"]
        request.headers["trakt-api-key"] = data["client_id"]
        request.register_hook("response", self.check_response)
        return request

    @staticmethod
    def check_response(response, **kwargs):
        if response.status_code == 401:
            raise ClickException("Trakt rejected the browser token. Update the token file from your signed-in browser; the request was not replayed.")
        if response.is_redirect:
            raise ClickException("Unexpected Trakt API redirect; browser credentials were not forwarded.")
        return response
