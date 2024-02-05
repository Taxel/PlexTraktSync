from urllib.parse import parse_qs, urlparse


def id_from_url(url: str):
    """
    Extracts id from urls like:
      https://app.plex.tv/desktop/#!/server/abcdefg/details?key=%2Flibrary%2Fmetadata%2F13202
      https://app.plex.tv/desktop/#!/server/abcdefg/playHistory?filters=metadataItemID%3D6041&filterTitle=&isParentType=false
      https://app.plex.tv/desktop/#!/provider/tv.plex.provider.discover/details?key=%2Flibrary%2Fmetadata%2F5d7768532e80df001ebe18e7
    """
    result = urlparse(url)
    if result.fragment[0] == "!":
        fragment = urlparse(result.fragment)
        parsed = parse_qs(fragment.query)
        if "key" in parsed:
            key = ",".join(parsed["key"])
            if key.startswith("/library/metadata/"):
                id = key[len("/library/metadata/"):]
                if fragment.path == "!/provider/tv.plex.provider.discover/details":
                    return f"https://metadata.provider.plex.tv/library/metadata/{id}"
                return int(id)
        if "filters" in parsed:
            filters = parse_qs(parsed["filters"][0])
            if "metadataItemID" in filters:
                return int(filters["metadataItemID"][0])

    return url


def plex_id(id):
    key = id.rsplit("/", 1)[-1]
    return f"https://metadata.provider.plex.tv/library/metadata/{key}"


def expand_plexid(input):
    from plextraktsync.plex.PlexIdFactory import PlexIdFactory

    for id in input:
        yield PlexIdFactory.create(id)


def expand_id(input):
    """
    Takes list of id or urls and resolves to Plex media id.
    """
    for id in input:
        if id.isnumeric():
            id = int(id)
        elif id.startswith("https:") or id.startswith("http:"):
            id = id_from_url(id)
        elif id.startswith("plex://"):
            id = plex_id(id)
        yield id
