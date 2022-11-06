"""Client for database with snapshot."""
import logging
from typing import Any, Dict, Iterator, List, Optional, Union

import pymongo
from bson.objectid import ObjectId

from wbm_newspapers.snapshot.snapshot import Snapshot

logger = logging.getLogger(__file__)


class DbClient:
    """Database client with snapshots."""

    CONNECTION = 'mongodb://localhost'
    DATABASE = 'anynews_wbm'

    def __init__(self,
                 connection: Optional[str] = None,
                 database: Optional[str] = None):
        """
        Parameters
        ----------
        connection : Optional[str], optional
            MongoDB connection string, by default None.
        database : Optional[str], optional
            Database name, by default None.
        """

        if connection is None:
            connection = self.CONNECTION

        if database is None:
            database = self.DATABASE

        self._client = pymongo.MongoClient(connection)
        self._db = self._client[self.DATABASE]

    @property
    def db(self):  # pylint: disable=invalid-name
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

    def __init__(self, db: DbClient, name: str):  # pylint: disable=invalid-name
        """
        Parameters
        ----------
        db : DbClient
            Database client object.
        name : str
            Name of the collection with articles.
        """
        self._db = db
        self._name = name

        self._collection = self._db.db[self.name]
        self._o_collection = self._db.db[self.name_origin]

    @property
    def db(self):  # pylint: disable=invalid-name
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
        """Get `pymongo` collection object."""
        return self._collection

    def document2snapshot(self, doc) -> Snapshot:
        """Convert document to `Snapshot` object."""
        item = {
            key: val for key, val in doc.items()
            if key not in self._special_fields
        }
        snapshot = Snapshot.from_dict(item)
        return snapshot

    def cursor2snapshots(self, cursor) -> List[Snapshot]:
        """Convert cursor to the list of snapshots."""
        result = []
        for item in cursor:
            snapshot = self.document2snapshot(item)
            result.append(snapshot)

        return result

    def find_keys(self, **kwargs) -> pymongo.cursor.Cursor:
        """Find snapshots """
        key_fields = Snapshot.key_fields()
        keys = set(kwargs) - set(key_fields)

        if len(keys) > 0:
            raise ValueError(f"Unknown keys {keys} not in {key_fields}")

        result = self._collection.find(kwargs)

        return result

    def find_field(self, field: str, regex: str) -> pymongo.cursor.Cursor:
        """
        Call mongodb find method in the collection
        and match by regular expression.

        Parameters
        ----------
        field : str
            Field name.
        regex : str
            Mongodb find regular expression.

        Returns
        -------
        pymongo.cursor.Cursor
            Cursor with found documents.
        """
        cursor = self._collection.find({field: {"$regex": regex}})
        return cursor

    def find_field_snapshot(self,
                            field: str,
                            regex: str) -> Iterator[Snapshot]:
        """
        Call mongodb find method in the collection
        and match by regular expression.


        Parameters
        ----------
        field : str
            Field name.
        regex : str
            Mongodb find regular expression.

        Yields
        ------
        Iterator[Snapshot]
            Iterator with snapshots.
        """
        cursor = self.find_field(field, regex)
        for doc in cursor:
            yield self.document2snapshot(doc)

    def all_titles(self):
        """Iterate over titles."""
        for doc in self._collection.find({}):
            yield doc["title"]

    def all_documents(self, fields: Dict[str, Any]) -> pymongo.cursor.Cursor:
        """Returns cursor over all documents."""
        return self._collection.find({}, projection=fields)

    def iterate_snapshots(self, query):
        """Iterate over snapshots using collection `find` method."""
        for doc in self._collection.find(query):
            yield self.document2snapshot(doc)

    def find_similar_cursor(self, snapshot: Snapshot) -> pymongo.cursor.Cursor:
        """Find similar snapshots using snapshots key fields."""
        dict_keys = snapshot.get_keys()
        result = self.find_keys(**dict_keys)
        return result

    def insert(self, snapshot: Snapshot, unique: bool = True):
        """
        Insert snapshot to the collection.

        Parameters
        ----------
        snapshot : Snapshot
            Snapshot object.
        unique : bool, optional
            Check snapshot keys existing in the collection.
            If exists then new snapshot won't be inserted.
            By default True.
        """

        has_similar = False
        if unique:
            similar_snapshots = self.find_similar_cursor(snapshot)
            has_similar = similar_snapshots.count() > 0

            logger.debug("Found similar snapshots: %d",
                         similar_snapshots.count())

        if not has_similar:
            data = snapshot.data_dict()
            self._collection.insert_one(data)
            logger.debug("Write to database")

    def find_original_url(self, url: str) -> List[Snapshot]:
        """Find original URL match."""
        cursor = self._collection.find({"original": url})
        result = self.cursor2snapshots(cursor)
        return result

    def get_ids(self, query: Optional[Dict[str, Any]] = None) -> List[str]:
        """Get ids selected by query"""
        if query is None:
            query = {}
        cursor = self._collection.find(query, projection={"_id": True})
        return [item["_id"] for item in cursor]

    def get_snapshots_by_id(self, id_: Union[str, ObjectId]) -> List[Snapshot]:
        """Get snapshot by its `_id` field in mongodb."""
        if isinstance(id_, str):
            id_ = ObjectId(id_)
        cursor = self._collection.find({"_id": id_})
        return self.cursor2snapshots(cursor)
