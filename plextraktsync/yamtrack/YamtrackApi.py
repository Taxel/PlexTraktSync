from __future__ import annotations

from datetime import datetime, timezone
from time import sleep
from typing import Any
from urllib.parse import urljoin

from click import ClickException
from requests import RequestException

from plextraktsync.factory import logging


class YamtrackApi:
    logger = logging.getLogger(__name__)
    MAX_RETRIES = 3
    PAGE_SIZE = 200

    def __init__(self, config: dict[str, Any], session):
        self.enabled = config["enabled"]
        self.url = (config["url"] or "").rstrip("/")
        self.timeout = config["timeout"]
        self.token = config["token"]
        self.session = session

        if self.enabled and not self.url:
            raise ClickException("Yamtrack is enabled but sync.yamtrack.url is not configured")
        if self.enabled and not self.token:
            raise ClickException("Yamtrack is enabled but YAMTRACK_TOKEN is not configured")

    @property
    def headers(self):
        return {
            "Accept": "application/json",
            "Authorization": f"******",
        }

    def movie_history(self, tmdb_id: int | str):
        return self._history(f"/api/v1/media/movie/tmdb/{tmdb_id}/history/")

    def episode_history(self, show_tmdb_id: int | str, season_number: int, episode_number: int):
        return self._history(f"/api/v1/media/tv/tmdb/{show_tmdb_id}/{season_number}/{episode_number}/history/")

    def add_movie_watch(self, tmdb_id: int | str, watched_at: datetime):
        return self._request(
            "post",
            "/api/v1/media/movie/",
            payload={
                "source": "tmdb",
                "media_id": str(tmdb_id),
                "status": 3,
                "end_date": self.normalize_datetime(watched_at),
            },
        )

    def add_episode_watch(self, show_tmdb_id: int | str, season_number: int, episode_number: int, watched_at: datetime):
        return self._request(
            "post",
            "/api/v1/media/episode/",
            payload={
                "source": "tmdb",
                "media_id": str(show_tmdb_id),
                "season_number": season_number,
                "episode_number": episode_number,
                "end_date": self.normalize_datetime(watched_at),
            },
        )

    def history_keys(self, entries: list[dict[str, Any]]):
        result = set()
        for entry in entries:
            date = entry.get("end_date") or entry.get("start_date") or entry.get("created")
            if date:
                result.add(self.normalize_datetime(date))
        return result

    def _history(self, path: str):
        offset = 0
        results = []
        while True:
            payload = self._request(
                "get",
                path,
                params={"limit": self.PAGE_SIZE, "offset": offset},
                allow_not_found=True,
            )
            if payload is None:
                return []

            page = payload.get("results", [])
            results.extend(page)

            pagination = payload.get("pagination", {})
            next_url = pagination.get("next")
            if not next_url or not page:
                return results

            offset += self.PAGE_SIZE

    def _request(self, method: str, path: str, payload: dict[str, Any] = None, params: dict[str, Any] = None, allow_not_found=False):
        if not self.enabled:
            return None

        url = urljoin(f"{self.url}/", path.lstrip("/"))

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    headers=self.headers,
                    json=payload,
                    params=params,
                    timeout=self.timeout,
                )
            except RequestException as exc:
                if attempt == self.MAX_RETRIES:
                    raise ClickException(f"Yamtrack request failed: {exc}") from exc
                self.logger.warning(f"Yamtrack request failed for {path}, retrying ({attempt}/{self.MAX_RETRIES}): {exc}")
                sleep(attempt)
                continue

            if response.status_code >= 500:
                if attempt == self.MAX_RETRIES:
                    raise ClickException(f"Yamtrack server error ({response.status_code}) for {path}")
                self.logger.warning(f"Yamtrack server error {response.status_code} for {path}, retrying ({attempt}/{self.MAX_RETRIES})")
                sleep(attempt)
                continue

            if allow_not_found and response.status_code == 404:
                return None
            if response.status_code == 409:
                return self._json(response)
            if response.status_code in (401, 403):
                raise ClickException("Yamtrack authentication failed")
            if response.status_code >= 400:
                detail = self._detail(response)
                raise ClickException(f"Yamtrack request failed ({response.status_code}): {detail}")

            return self._json(response)

        return None

    @staticmethod
    def _json(response):
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            return {}

    def _detail(self, response):
        payload = self._json(response)
        if isinstance(payload, dict) and "detail" in payload:
            return payload["detail"]
        return response.text or "Unknown error"

    @classmethod
    def normalize_datetime(cls, value: datetime | str):
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
