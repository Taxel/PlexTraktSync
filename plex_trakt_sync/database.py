import sqlite3
from datetime import datetime
from typing import Union

from plexapi.server import PlexServer
from plexapi.video import Movie, Episode

from plex_trakt_sync.logging import logger
from plex_trakt_sync.media import Media


class Database(object):
    _uncommited = False

    def __init__(self, database_path: str):
        try:
            self.filename = database_path
            self._connection = sqlite3.connect(database_path)
            self._cursor = self._connection.cursor()
            self._cursor.execute('ANALYZE')

        except sqlite3.OperationalError as e:
            logger.error(e)
            raise e

        except sqlite3.DatabaseError as e:
            logger.error(e)
            raise e

    @property
    def cursor(self):
        return self._cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._uncommited:
            self.commit()

        self._connection.close()

    def execute(self, query, *args):
        self._uncommited = True
        return self.cursor.execute(query, *args)

    def commit(self):
        self._connection.commit()
        self._uncommited = False

    def rollback(self):
        self._connection.rollback()
        self._uncommited = False

    def has_uncommited(self):
        return self._uncommited

    def format_time(self, time: datetime):
        """
        Format datetime for sqlite, Plex dates are in localtime.
        """
        return time.astimezone().replace(tzinfo=None).isoformat(' ', timespec='seconds')


class PlexDatabase:
    _insert_watched = """
        INSERT INTO metadata_item_views (
            account_id,
            guid,
            metadata_type,
            library_section_id,
            grandparent_title,
            parent_index,
            parent_title,
            "index",
            title,
            thumb_url,
            viewed_at,
            grandparent_guid,
            originally_available_at,
            device_id
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """

    _update_metadata_item_settings = """
        UPDATE metadata_item_settings
        SET
            view_count = view_count+1,
            last_viewed_at = ?
        WHERE
            guid = ?
    """

    def __init__(self, db: Database):
        self.db = db

    def mark_watched(self, media: Media, time: datetime):
        plex: PlexServer = media.plex_api.plex
        pm: Union[Movie, Episode] = media.plex.item

        account = plex.systemAccount(0)
        device = plex.systemDevice(1)

        account_id = account.id
        device_id = device.id
        metadata_type = 1
        library_section_id = pm.librarySectionID
        grandparent_title = None
        parent_index = -1
        parent_title = None
        index = 1
        title = pm.title
        thumb_url = None
        grandparent_guid = None

        with self.db as db:
            originally_available_at = db.format_time(pm.originallyAvailableAt)
            viewed_at = db.format_time(time)
            db.execute(self._insert_watched, (
                account_id,
                media.plex.guid,
                metadata_type,
                library_section_id,
                grandparent_title,
                parent_index,
                parent_title,
                index,
                title,
                thumb_url,
                viewed_at,
                grandparent_guid,
                originally_available_at,
                device_id
            ))
            db.execute(self._update_metadata_item_settings, (
                viewed_at,
                media.plex.guid,
            ))
