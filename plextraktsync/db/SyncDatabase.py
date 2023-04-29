from plextraktsync.db.Database import Database


class SyncDatabase:
    table_name = "sync"
    # fields:
    # A. Media ID
    # B. Plex timestamp watched
    # C. seen on Plex sync?
    # D. Trakt timestamp watched
    # E. seen on Trakt sync?
    # F. result
    schema = """
        id PRIMARY KEY,
        media_id,
        plex_timestamp_watched,
        seen_on_plex_sync,
        trakt_timestamp_watched,
        seen_on_trakt_sync,
        result
    """

    def __init__(self, con: Database):
        self.con = con
        with self.con as con:
            self._create_table(con)

    # Initial CREATE TABLE must happen in shared connection; subsequent queries will use thread-local connections
    def _create_table(self, con: Database):
        con.execute(f'CREATE TABLE IF NOT EXISTS {self.table_name} ({self.schema})')

    def insert(self, record: SyncRecord):
        pass
