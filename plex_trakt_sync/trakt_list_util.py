from trakt.users import UserList
from trakt.errors import NotFoundException, OAuthException
from trakt.movies import Movie
from trakt.tv import TVEpisode
from plexapi.video import Episode
from plex_trakt_sync.requests_cache import requests_cache
from plex_trakt_sync.logging import logger
from plexapi.exceptions import BadRequest, NotFound
from itertools import count


class TraktList():
    def __init__(self, username, listname):
        self.name = listname
        self.plex_items = []
        if username is not None:
            self.trakt_items = dict(zip([(elem.media_type, elem.trakt) for elem in UserList._get(listname, username)._items if isinstance(elem, (Movie, TVEpisode))], count(1)))

    @staticmethod
    def from_trakt_list(listname, trakt_list):
        l = TraktList(None, listname)
        l.trakt_items = dict(zip([(elem.media_type, elem.trakt) for elem in trakt_list], count(1)))
        return l

    def addPlexItem(self, trakt_item, plex_item):
        rank = self.trakt_items.get((trakt_item.media_type, trakt_item.trakt))
        if rank is not None:
            self.plex_items.append((rank, plex_item))
            if isinstance(plex_item, Episode):
                logger.info('Show [{} ({})]: {} added to list {}'.format(plex_item.show().title, plex_item.show().year, plex_item.seasonEpisode, self.name))
            else:
                logger.info('Movie [{} ({})]: added to list {}'.format(plex_item.title, plex_item.year, self.name))

    def updatePlexList(self, plex):
        with requests_cache.disabled():
            try:
                plex.playlist(self.name).delete()
            except (NotFound, BadRequest):
                logger.debug("Playlist %s not found, so it could not be deleted. Actual playlists: %s" % (self.name, plex.playlists()))
                pass
            if len(self.plex_items) > 0:
                _, plex_items_sorted = zip(*sorted(dict(reversed(self.plex_items)).items()))
                plex.createPlaylist(self.name, items=plex_items_sorted)


class TraktListUtil():
    def __init__(self):
        self.lists = []

    def addList(self, username, listname, trakt_list=None):
        if trakt_list is not None:
            self.lists.append(TraktList.from_trakt_list(listname, trakt_list))
            logger.info("Downloaded List {}".format(listname))
            return
        try:
            self.lists.append(TraktList(username, listname))
            logger.info("Downloaded List {}".format(listname))
        except (NotFoundException, OAuthException):
            logger.warning("Failed to get list {} by user {}".format(listname, username))

    def addPlexItemToLists(self, m):
        for l in self.lists:
            l.addPlexItem(m.trakt, m.plex.item)

    def updatePlexLists(self, plex):
        for l in self.lists:
            l.updatePlexList(plex)
