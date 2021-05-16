import sqlite3

from plex_trakt_sync.logging import logger


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
