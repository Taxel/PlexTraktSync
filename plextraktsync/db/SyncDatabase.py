from plextraktsync.db.Database import Database


class SyncDatabase:
    def __init__(self, con: Database):
        self.con = con
