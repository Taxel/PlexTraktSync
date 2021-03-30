from trakt.users import UserList
from trakt.errors import NotFoundException, OAuthException
from trakt.movies import Movie
from trakt.tv import TVEpisode
from plexapi.video import Episode
import requests_cache
import logging
from plexapi.exceptions import BadRequest, NotFound
from itertools import count


class TraktList():
    def __init__(self, username, listname):
        self.name = listname
        self.plex_items = []
        if username is not None:
            self.traktids = dict(zip(map(lambda e: e.trakt, [elem for elem in UserList._get(listname, username).get_items() if isinstance(elem, (Movie, TVEpisode))]), count(1)))

    @staticmethod
    def from_traktid_list(listname, traktid_list):
        l = TraktList(None, listname)
        l.traktids = dict(zip(traktid_list, count(1)))
        return l

    def addPlexItem(self, traktid, plex_item):
        rank = self.traktids.get(traktid)
        if rank is not None:
            self.plex_items.append((rank, plex_item))
            if isinstance(plex_item, Episode):
                logging.info('Show [{} ({})]: {} added to list {}'.format(plex_item.show().title, plex_item.show().year, plex_item.seasonEpisode, self.name))
            else:
                logging.info('Movie [{} ({})]: added to list {}'.format(plex_item.title, plex_item.year, self.name))

    def updatePlexList(self, plex):
        with requests_cache.disabled():
            try:
                plex.playlist(self.name).delete()
            except (NotFound, BadRequest):
                logging.error("Playlist %s not found, so it could not be deleted. Actual playlists: %s" % (self.name, plex.playlists()))
                pass
            if len(self.plex_items) > 0:
                _, plex_items_sorted = zip(*sorted(dict(reversed(self.plex_items)).items()))
                plex.createPlaylist(self.name, items=plex_items_sorted)


class TraktListUtil():
    def __init__(self):
        self.lists = []

    def addList(self, username, listname, traktid_list=None):
        if traktid_list is not None:
            self.lists.append(TraktList.from_traktid_list(listname, traktid_list))
            logging.info("Downloaded List {}".format(listname))
            return
        try:
            self.lists.append(TraktList(username, listname))
            logging.info("Downloaded List {}".format(listname))
        except (NotFoundException, OAuthException):
            logging.warning("Failed to get list {} by user {}".format(listname, username))

    def addPlexItemToLists(self, traktid, plex_item):
        for l in self.lists:
            l.addPlexItem(traktid, plex_item)

    def updatePlexLists(self, plex):
        for l in self.lists:
            l.updatePlexList(plex)
