import sqlite3
from datetime import datetime

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
        account_id = 1
        metadata_type = 1
        library_section_id = 2
        grandparent_title = ''
        parent_index = -1
        parent_title = ''
        index = 1
        title = 'Coma'
        thumb_url = 'metadata://posters/com.plexapp.agents.imdb_3eea3b08fc7094167eee68cca64f8be407be0cbe'
        grandparent_guid = ''
        originally_available_at = '2019-11-19 00:00:00'
        device_id = 20

        with self.db as db:
            viewed_at = db.format_time(time)
            db.cursor.execute(self._insert_watched, (
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
            db.cursor.execute(self._update_metadata_item_settings, (
                time,
                media.plex.guid,
            ))
