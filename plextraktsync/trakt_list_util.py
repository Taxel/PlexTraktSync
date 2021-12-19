from itertools import count

from plexapi.video import Episode
from trakt.core import get
from trakt.errors import NotFoundException, OAuthException
from trakt.movies import Movie
from trakt.tv import TVEpisode
from trakt.users import UserList
from trakt.utils import extract_ids, slugify

from plextraktsync.logging import logger
from plextraktsync.plex_api import PlexApi


class LazyUserList(UserList):
    @get
    def get_items(self):
        data = yield 'users/{user}/lists/{id}/items'.format(
            user=slugify(self.creator), id=self.slug)
        for item in data:
            if 'type' not in item:
                continue
            item_type = item['type']
            item_data = item.pop(item_type)
            extract_ids(item_data)
            self._items.append((item_type + 's', item_data['trakt']))
        yield self._items

    @classmethod
    @get
    def _get(cls, title, creator):
        data = yield 'users/{user}/lists/{id}'.format(user=slugify(creator),
                                                      id=slugify(title))
        extract_ids(data)
        ulist = LazyUserList(creator=creator, **data)
        ulist.get_items()
        yield ulist


class TraktList():
    def __init__(self, username, listname):
        self.name = listname
        self.plex_items = []
        if username is not None:
            prelist = [(elem[0], elem[1]) for elem in LazyUserList._get(listname, username)._items if elem[0] in ["movies", "episodes"]]
            self.trakt_items = dict(zip(prelist, count(1)))

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
                logger.info(f"Added to list {self.name}: {plex_item.show()}: {plex_item.seasonEpisode}")
            else:
                logger.info(f"Added to list {self.name}: {plex_item}")

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
