import sqlite3

from plextraktsync.factory import logging


class Database:
    _uncommited = False

    def __init__(self, database_path: str):
        self.logger = logging.getLogger("PlexTraktSync.Database")
        try:
            self.filename = database_path
            self._connection = sqlite3.connect(database_path)
            self._cursor = self._connection.cursor()
            self._cursor.execute('ANALYZE')

        except sqlite3.OperationalError as e:
            self.logger.error(e)
            raise e

        except sqlite3.DatabaseError as e:
            self.logger.error(e)
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
