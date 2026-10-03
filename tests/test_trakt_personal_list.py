from __future__ import annotations

from trakt.movies import Movie
from trakt.users import UserList

from plextraktsync.trakt.TraktUserList import TraktUserList


def make_user_list(items):
    """A real pytrakt UserList, filled the way UserList.get() fills it."""
    user_list = UserList(
        ids={"trakt": 1, "slug": "my-list"},
        name="My List",
        description="a description",
        privacy="private",
        share_link="",
        type="personal",
        display_numbers=True,
        allow_comments=False,
        sort_by="rank",
        sort_how="asc",
        created_at="",
        updated_at="",
        item_count=len(items),
        comment_count=0,
        likes=0,
        user=None,
    )
    user_list._items.extend(items)
    return user_list


class FakeTraktApi:
    def __init__(self, user_list):
        self.user_list = user_list

    @property
    def me(self):
        class Me:
            username = "someone"

        return Me()

    def get_personal_list(self, username, listname):
        return self.user_list


def test_personal_list_is_downloaded(monkeypatch):
    movies = [
        Movie("Arrival", year=2016, ids={"trakt": 10, "slug": "arrival-2016"}),
        Movie("Dune", year=2021, ids={"trakt": 20, "slug": "dune-2021"}),
    ]
    monkeypatch.setattr(
        "plextraktsync.factory.factory.trakt_api",
        FakeTraktApi(make_user_list(movies)),
        raising=False,
    )
    tl = TraktUserList(trakt_id=1, name="My List", username="someone", list_type="personal")

    description, items = tl.load_items()

    assert description == "a description"
    assert items == {("movies", 10): 1, ("movies", 20): 2}
