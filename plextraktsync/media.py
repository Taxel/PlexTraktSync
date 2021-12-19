from plexapi.exceptions import PlexApiException
from requests import RequestException
from trakt.errors import TraktException

from plextraktsync.logging import logger
from plextraktsync.plex_api import PlexApi, PlexGuid, PlexLibraryItem
from plextraktsync.trakt_api import TraktApi


class Media:
    """
    Class containing Plex and Trakt media items (Movie, Episode)
    """

    def __init__(self, plex, trakt, plex_api: PlexApi = None, trakt_api: TraktApi = None):
        self.plex_api = plex_api
        self.trakt_api = trakt_api
        self.plex = plex
        self.trakt = trakt
        self.show = None

    @property
    def season_number(self):
        return self.plex.season_number

    @property
    def episode_number(self):
        return self.plex.episode_number

    @property
    def trakt_id(self):
        return self.trakt.trakt

    @property
    def plex_url(self):
        return self.plex_api.media_url(self.plex)

    @property
    def trakt_url(self):
        return f"https://trakt.tv/{self.trakt.media_type}/{self.trakt_id}"

    @property
    def show_trakt_id(self):
        if not self.show:
            raise RuntimeError(f"Unexpected call: episode without show property")
        return self.show.trakt_id

    @property
    def is_movie(self):
        return self.plex.type == "movie"

    @property
    def is_episode(self):
        return self.plex.type == "episode"

    @property
    def is_collected(self):
        if self.is_movie:
            return self.trakt_id in self.trakt_api.movie_collection_set

        collected = self.trakt_api.collected(self.show.trakt)
        return collected.get_completed(self.season_number, self.episode_number)

    def add_to_collection(self):
        self.trakt_api.add_to_collection(self.trakt, self.plex)

    @property
    def watched_on_plex(self):
        return self.plex.item.isWatched

    @property
    def watched_on_trakt(self):
        if self.is_movie:
            return self.trakt_id in self.trakt_api.watched_movies

        watched = self.trakt_api.watched_shows
        return watched.get_completed(self.show_trakt_id, self.season_number, self.episode_number)

    def mark_watched_trakt(self):
        if self.is_movie:
            self.trakt_api.mark_watched(self.trakt, self.plex.seen_date)
        if self.is_episode:
            self.trakt_api.mark_watched(self.trakt, self.plex.seen_date, self.show_trakt_id)

    def mark_watched_plex(self):
        self.plex_api.mark_watched(self.plex.item)

    @property
    def trakt_rating(self):
        if self.trakt.media_type == 'movies':
            rating = self.trakt_api.movie_ratings.get(self.trakt.trakt, None)
        elif self.trakt.media_type == 'episodes':
            rating = self.trakt_api.episode_ratings.get(self.trakt.trakt, None)
        else:
            raise RuntimeError(f"Unsupported media type: {self.trakt.media_type}")
        if rating:
            return int(rating)
        return None

    @property
    def plex_rating(self):
        return self.plex.rating

    def trakt_rate(self):
        self.trakt_api.rate(self.trakt, self.plex_rating)

    def plex_rate(self):
        self.plex_api.rate(self.plex.item, self.trakt_rating)

    def plex_history(self, **kwargs):
        yield from self.plex_api.history(self.plex.item, **kwargs)

    def __str__(self):
        return str(self.plex)


class MediaFactory:
    """
    Class that is able to resolve Trakt media item from Plex media item and return generic Media class
    """

    def __init__(self, plex: PlexApi, trakt: TraktApi):
        self.plex = plex
        self.trakt = trakt

    def resolve_any(self, pm: PlexLibraryItem, tm=None):
        try:
            guids = pm.guids
        except (PlexApiException, RequestException) as e:
            logger.error(f"Skipping {pm}: {e}")
            return None

        for guid in guids:
            m = self.resolve_guid(guid, tm)
            if m:
                return m

        return None

    def resolve_guid(self, guid: PlexGuid, tm=None):
        if guid.provider in ["local", "none", "agents.none"]:
            logger.warning(f"{guid.pm.item}: Skipping guid {guid} because provider {guid.provider} has no external Id")

            return None

        if guid.provider not in ["imdb", "tmdb", "tvdb"]:
            logger.error(
                f"{guid.pm.item}: Unable to parse a valid provider from guid {guid}"
            )
            return None

        try:
            if tm:
                tm = self.trakt.find_episode_guid(tm, guid)
            else:
                tm = self.trakt.find_by_guid(guid)
        except (TraktException, RequestException) as e:
            logger.warning(f"{guid.pm.item}: Skipping guid {guid} Trakt errors: {e}")
            return None

        if tm is None:
            logger.warning(f"{guid.pm.item}: Skipping guid {guid} not found on Trakt")
            return None

        return Media(guid.pm, tm, plex_api=self.plex, trakt_api=self.trakt)
