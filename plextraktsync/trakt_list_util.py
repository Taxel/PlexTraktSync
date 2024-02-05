from __future__ import annotations

from trakt.core import get
from trakt.users import UserList


class LazyUserList(UserList):
    @get
    def get_items(self):
        data = yield f"lists/{self.trakt}/items"
        for item in data:
            if "type" not in item:
                continue
            item_type = item["type"]
            item_data = item.pop(item_type)
            self._items.append((item_type + "s", item_data["ids"]["trakt"]))
        yield self._items

    @classmethod
    @get
    def _get(cls, title, id):
        data = yield f"lists/{id}"
        ulist = cls(creator=data["user"]["username"], **data)
        ulist.get_items()
        yield ulist
