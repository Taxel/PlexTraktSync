from plextraktsync.db.Database import Database


class SyncDatabase:
    table_name = 'sync'

    def __init__(self, con: Database):
        self.con = con
        with self.con as con:
            self._create_table(con)

    # Initial CREATE TABLE must happen in shared connection; subsequent queries will use thread-local connections
    def _create_table(self, con: Database):
        con.execute(f'CREATE TABLE IF NOT EXISTS {self.table_name} ({self.schema})')

    def insert(self, record: SyncRecord):
        pass
