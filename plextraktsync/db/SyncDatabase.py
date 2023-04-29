from plextraktsync.db.Database import Database


class SyncDatabase:
    def __init__(self, db: Database):
        self.db = db
