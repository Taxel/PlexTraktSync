from plex_trakt_sync.main import get_plex_server
from plex_trakt_sync.config import CONFIG


class PlexApi:
    """
    Plex API class abstracting common data access and dealing with requests cache.
    """

    @property
    def plex_server(self):
        return get_plex_server()

    @property
    def library_sections(self):
        result = []
        for section in self.plex_server.library.sections():
            if section.title in CONFIG["excluded-libraries"]:
                continue
            result.append(section)

        return result
