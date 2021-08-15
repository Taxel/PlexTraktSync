from itertools import count

from plexapi.video import Episode
from trakt.errors import NotFoundException, OAuthException
from trakt.movies import Movie
from trakt.tv import TVEpisode
from trakt.users import UserList

from plex_trakt_sync.logging import logger
from plex_trakt_sync.plex_api import PlexApi


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

    def updatePlexList(self, plex: PlexApi):
        plex.delete_playlist(self.name)

        if len(self.plex_items) > 0:
            plex.create_playlist(self.name, self.plex_items)


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

    def updatePlexLists(self, plex: PlexApi):
        for l in self.lists:
            l.updatePlexList(plex)
