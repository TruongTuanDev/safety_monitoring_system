from pymongo import MongoClient


class DatabaseClient:
    """Simple MongoDB client wrapper."""

    def __init__(self, uri: str = 'mongodb://localhost:27017', db_name: str = 'safety_monitoring'):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]

    def users(self):
        return self.db['users']

    def close(self):
        if self.client:
            self.client.close()
