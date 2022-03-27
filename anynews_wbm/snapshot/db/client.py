"""Client for database with snapshot."""
import logging
from typing import List, Optional

import pymongo
from anynews_wbm.snapshot.snapshot import Snapshot

logger = logging.getLogger(__file__)


class DbClient:
    """Database client with snapshots."""

    CONNECTION = 'mongodb://localhost'
    DATABASE = 'anynews_wbm'

    def __init__(self,
                 connection: Optional[str] = None,
                 database: Optional[str] = None):

        if connection is None:
            connection = self.CONNECTION

        if database is None:
            database = self.DATABASE

        self._client = pymongo.MongoClient(connection)
        self._db = self._client[self.DATABASE]

    @property
    def db(self):
        """Return database object."""
        return self._db

    @property
    def client(self) -> pymongo.MongoClient:
        """Mongodb client."""
        return self._client

    def collection_names(self):
        """Collections names."""
        return self._db.collection_names()


class SnapshotCollectionClient:
    """Snapshot collection functions."""

    _origin_postfix: str = "_origin"
    _special_fields = ['_id']

    def __init__(self, db: DbClient, name: str):
        self._db = db
        self._name = name

        self._collection = self._db.db[self.name]
        self._o_collection = self._db.db[self.name_origin]

    @property
    def db(self):
        """Get database object."""
        return self._db

    @property
    def name(self):
        """Collection name."""
        return self._name

    @property
    def name_origin(self):
        """Origin collection name."""
        return f"{self._name}{self._origin_postfix}"

    @property
    def collection(self) -> pymongo.collection.Collection:
        return self._collection

    def document2snapshot(self, doc) -> Snapshot:
        item = {
            key: val for key, val in doc.items()
            if key not in self._special_fields
        }
        snapshot = Snapshot.from_dict(item)
        return snapshot

    def cursor2snapshots(self, cursor) -> List[Snapshot]:

        result = []
        for item in cursor:
            snapshot = self.document2snapshot(item)
            result.append(snapshot)

        return result

    def find_keys(self, **kwargs) -> pymongo.cursor.Cursor:

        key_fields = Snapshot.key_fields()
        keys = set(kwargs) - set(key_fields)

        if len(keys) > 0:
            raise ValueError(f"Unknown keys {keys} not in {key_fields}")

        result = self._collection.find(kwargs)

        return result

    def find_datetime_cursor(self, query: str) -> pymongo.cursor.Cursor:
        cursor = self._collection.find({"title": {"$regex": query}})
        return cursor

    def find_title_cursor(self, query: str) -> pymongo.cursor.Cursor:
        cursor = self._collection.find({"title": {"$regex": query}})
        return cursor

    def all_titles(self):
        for doc in self._collection.find({}):
            yield doc["title"]

    def all_documents(self):
        return self._collection.find({})

    def iterate_snapshots(self, query):
        for doc in self._collection.find(query):
            yield self.document2snapshot(doc)

    def find_title(self, query: str) -> List[Snapshot]:

        cursor = self.find_title_cursor(query)
        result = self.cursor2snapshots(cursor)

        return result

    def find_similar_cursor(self, snapshot: Snapshot) -> pymongo.cursor.Cursor:
        dict_keys = snapshot.get_keys()
        result = self.find_keys(**dict_keys)
        return result

    def insert(self, snapshot: Snapshot, unique: bool = True):

        has_similar = False
        if unique:
            similar_snapshots = self.find_similar_cursor(snapshot)
            has_similar = similar_snapshots.count() > 0

            logger.debug("Found similar snapshots: %d",
                         similar_snapshots.count())

        if not has_similar:
            data = snapshot.data_dict()
            self._collection.insert_one(data)
            snapshot = snapshot.snapshot_dict()
            self._o_collection.insert_one(snapshot)
            logger.debug("Write to database")

    def find_original_url(self, url: str) -> List[Snapshot]:
        cursor = self._collection.find({"original": url})
        result = self.cursor2snapshots(cursor)
        return result
