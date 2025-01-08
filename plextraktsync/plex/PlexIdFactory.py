from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from .PlexId import PlexId


class PlexIdFactory:
    @classmethod
    def create(cls, key: str | int):
        if isinstance(key, int) or key.isnumeric():
            return PlexId(int(key))
        elif key.startswith("https://trakt.tv/"):
            return cls.from_trakt_url(key)
        elif key.startswith("https://l.plex.tv/"):
            return cls.from_plex_redirect_url(key)
        elif key.startswith("https://watch.plex.tv/"):
            return cls.from_plex_watch_url(key)
        elif key.startswith("https:") or key.startswith("http:"):
            return cls.from_url(key)
        elif key.startswith("plex://"):
            return cls.from_plex_guid(key)

        raise RuntimeError(f"Unable to create PlexId: {key}")

    @classmethod
    def from_plex_guid(cls, id):
        key = id.rsplit("/", 1)[-1]
        return PlexId(key, provider=PlexId.METADATA)

    @staticmethod
    def from_url(url: str):
        """
        Extracts id from urls like:
          https://app.plex.tv/desktop/#!/server/abcdefg/details?key=%2Flibrary%2Fmetadata%2F13202
          https://app.plex.tv/desktop/#!/server/abcdefg/playHistory?filters=metadataItemID%3D6041&filterTitle=&isParentType=false
          https://app.plex.tv/desktop/#!/provider/tv.plex.provider.discover/details?key=%2Flibrary%2Fmetadata%2F5d7768532e80df001ebe18e7
          https://app.plex.tv/desktop/#!/provider/tv.plex.provider.discover/details?key=/library/metadata/5d776a8e51dd69001fe24eb8'
          https://app.plex.tv/desktop/#!/provider/tv.plex.provider.vod/details?key=%2Flibrary%2Fmetadata%2F5d776b1cad5437001f7936f4
        """

        result = urlparse(url)
        if result.fragment[0] != "!":
            raise RuntimeError(f"Unable to parse: {url}")

        fragment = urlparse(result.fragment)
        parsed = parse_qs(fragment.query)

        if fragment.path.startswith("!/server/"):
            server = fragment.path.split("/")[2]
        else:
            server = None

        if "key" in parsed:
            key = ",".join(parsed["key"])
            if key.startswith("/library/metadata/"):
                id = key[len("/library/metadata/") :]
                if fragment.path == "!/provider/tv.plex.provider.discover/details":
                    return PlexId(id, provider=PlexId.METADATA)
                if fragment.path == "!/provider/tv.plex.provider.vod/details":
                    return PlexId(id, provider=PlexId.METADATA)
                return PlexId(int(id), server=server)

        if "filters" in parsed:
            filters = parse_qs(parsed["filters"][0])
            if "metadataItemID" in filters:
                return PlexId(int(filters["metadataItemID"][0]), server=server)

        raise RuntimeError(f"Unable to parse: {url}")

    @classmethod
    def from_trakt_url(cls, url: str):
        path = urlparse(url).path

        if path.startswith("/movies/"):
            media_type = "movie"
            slug = path[len("/movies/") :]
        else:
            from click import ClickException

            raise ClickException(f"Unable to create PlexId: {path}")

        from plextraktsync.factory import factory
        from plextraktsync.trakt.TraktItem import TraktItem

        tm = TraktItem(factory.trakt_api.find_by_slug(slug, media_type))
        results = factory.plex_api.search_by_guid(tm.guids, libtype=tm.type)
        if results is None:
            raise RuntimeError(f"Unable to find Plex Match: {url}")
        if len(results) > 1:
            raise RuntimeError(f"Failed to find unique match: {url}")
        pm = results[0]

        return PlexId(pm.key, server=pm.plex.server.machineIdentifier)

    @classmethod
    def from_plex_watch_url(cls, url: str):
        """
        Extracts id from urls like:
            https://watch.plex.tv/movie/heavier-trip
        """

        query = parse_qs(urlparse(url).query)
        if "utm_content" not in query:
            raise RuntimeError(f"Required 'utm_content' query missing from url: {url}")

        plex_id = ",".join(query["utm_content"])
        key = f"/library/metadata/{plex_id}"
        location = f"https://app.plex.tv/desktop/#!/provider/tv.plex.provider.discover/details?key={key}"

        return cls.create(location)

    @classmethod
    def from_plex_redirect_url(cls, url: str):
        """
        Extracts id from urls like:
            https://l.plex.tv/Nd7JNtC
        """
        from plextraktsync.factory import factory

        session = factory.session
        response = session.head(url)
        location = session.get_redirect_target(response)
        if location is None:
            raise RuntimeError(f"Failed to find redirect from url: {url}")

        return cls.create(location)
