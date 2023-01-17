from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.cached_property import cached_property

if TYPE_CHECKING:
    from plextraktsync.config.Config import Config


class SyncConfig:
    def __init__(self, config: Config):
        self.config = dict(config["sync"])

    def __getitem__(self, key):
        return self.config[key]

    def __contains__(self, key):
        return key in self.config

    def get(self, section, key):
        return self[key] if key in self else self[section][key]

    @cached_property
    def trakt_to_plex(self):
        return {
            "watched_status": self.get("trakt_to_plex", "watched_status"),
            "ratings": self.get("trakt_to_plex", "ratings"),
            "liked_lists": self.get("trakt_to_plex", "liked_lists"),
            "watchlist": self.get("trakt_to_plex", "watchlist"),
            "watchlist_as_playlist": self.get("trakt_to_plex", "watchlist_as_playlist"),
        }

    @cached_property
    def plex_to_trakt(self):
        return {
            "watched_status": self.get("plex_to_trakt", "watched_status"),
            "ratings": self.get("plex_to_trakt", "ratings"),
            "collection": self.get("plex_to_trakt", "collection"),
            "watchlist": self.get("plex_to_trakt", "watchlist"),
        }

    @cached_property
    def sync_ratings(self):
        return self.trakt_to_plex["ratings"] or self.plex_to_trakt["ratings"]

    @cached_property
    def sync_watchlists(self):
        return self.trakt_to_plex["watchlist"] or self.plex_to_trakt["watchlist"]

    @cached_property
    def clear_collected(self):
        return self.plex_to_trakt["collection"] and self["plex_to_trakt"]["clear_collected"]

    @cached_property
    def sync_watched_status(self):
        return self.trakt_to_plex["watched_status"] or self.plex_to_trakt["watched_status"]

    @cached_property
    def update_plex_wl(self):
        return self.trakt_to_plex["watchlist"] and not self.trakt_to_plex["watchlist_as_playlist"]

    @cached_property
    def update_plex_wl_as_pl(self):
        return self.trakt_to_plex["watchlist"] and self.trakt_to_plex["watchlist_as_playlist"]

    @cached_property
    def update_trakt_wl(self):
        return self.plex_to_trakt["watchlist"]

    @cached_property
    def sync_wl(self):
        return self.update_plex_wl or self.update_trakt_wl

    @cached_property
    def sync_liked_lists(self):
        return self.trakt_to_plex["liked_lists"]

    @cached_property
    def need_library_walk(self):
        return any([
            self.update_plex_wl_as_pl,
            self.sync_watched_status,
            self.sync_ratings,
            self.plex_to_trakt["collection"],
            self.sync_liked_lists,
        ])
