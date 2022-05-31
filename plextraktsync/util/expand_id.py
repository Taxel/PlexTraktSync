from urllib.parse import parse_qs, urlparse


def id_from_url(url: str):
    """
    Extracts id from urls like:
      https://app.plex.tv/desktop/#!/server/abcdefg/details?key=%2Flibrary%2Fmetadata%2F13202
      https://app.plex.tv/desktop/#!/server/abcdefg/playHistory?filters=metadataItemID%3D6041&filterTitle=&isParentType=false
    """
    result = urlparse(url)
    if result.fragment[0] == "!":
        parsed = parse_qs(urlparse(result.fragment).query)
        if "key" in parsed:
            key = ",".join(parsed["key"])
            if key.startswith("/library/metadata/"):
                return int(key[len("/library/metadata/"):])
        if "filters" in parsed:
            filters = parse_qs(parsed["filters"][0])
            if "metadataItemID" in filters:
                return int(filters["metadataItemID"][0])

    return url


def expand_id(input):
    """
    Takes list of id or urls and resolves to Plex media id.
    """
    for id in input:
        if id.isnumeric():
            id = int(id)
        elif id.startswith("https:") or id.startswith("http:"):
            id = id_from_url(id)
        yield id
