from itertools import count

from plexapi.video import Episode
from trakt.core import get
from trakt.errors import NotFoundException, OAuthException
from trakt.users import UserList
from trakt.utils import extract_ids, slugify

from plextraktsync.factory import logger


class LazyUserList(UserList):
    @get
    def get_items(self):
        data = yield f"users/{slugify(self.creator)}/lists/{self.slug}/items"
        for item in data:
            if "type" not in item:
                continue
            item_type = item["type"]
            item_data = item.pop(item_type)
            extract_ids(item_data)
            self._items.append((item_type + "s", item_data["trakt"]))
        yield self._items

    @classmethod
    @get
    def _get(cls, title, creator):
        data = yield f"users/{slugify(creator)}/lists/{slugify(title)}"
        extract_ids(data)
        ulist = LazyUserList(creator=creator, **data)
        ulist.get_items()
        yield ulist


class TraktList:
    def __init__(self, username, listname):
        self.name = listname
        self.plex_items = []
        if username is not None:
            prelist = [
                (elem[0], elem[1])
                for elem in LazyUserList._get(listname, username)._items
                if elem[0] in ["movies", "episodes"]
            ]
            self.trakt_items = dict(zip(prelist, count(1)))

    @staticmethod
    def from_trakt_list(listname, trakt_list):
        tl = TraktList(None, listname)
        tl.trakt_items = dict(
            zip([(elem.media_type, elem.trakt) for elem in trakt_list], count(1))
        )
        return tl

    def addPlexItem(self, trakt_item, plex_item):
        rank = self.trakt_items.get((trakt_item.media_type, trakt_item.trakt))
        if rank is not None:
            self.plex_items.append((rank, plex_item))
            if isinstance(plex_item, Episode):
                logger.info(
                    f"Added to list {self.name}: {plex_item.show()}: {plex_item.seasonEpisode}"
                )
            else:
                logger.info(f"Added to list {self.name}: {plex_item}")


class TraktListUtil:
    def __init__(self):
        self.lists = []

    def addList(self, username, listname, trakt_list=None):
        if trakt_list is not None:
            self.lists.append(TraktList.from_trakt_list(listname, trakt_list))
            logger.info(f"Downloaded List {listname}")
            return
        try:
            self.lists.append(TraktList(username, listname))
            logger.info(f"Downloaded List {listname}")
        except (NotFoundException, OAuthException):
            logger.warning(
                f"Failed to get list {listname} by user {username}"
            )

    def addPlexItemToLists(self, m):
        for tl in self.lists:
            tl.addPlexItem(m.trakt, m.plex.item)
