"""Database interface for spiders."""
from wbm_newspapers.snapshot.db.client import DbClient, SnapshotCollectionClient
from wbm_newspapers.waybackmachine.spiders.response import \
    WaybackMachineResponseCDX


class SpiderDatabase:
    """Database object which works in spiders."""

    def __init__(self,
                 name: str,
                 host: str = 'mongodb://localhost',
                 database: str = 'anynews_wbm'):
        """
        Parameters
        ----------
        name : str
            Spider name.
        host : _type_, optional
            MongoDB host string, by default 'mongodb://localhost'.
        database : str, optional
            MongoDB database name, by default 'anynews_wbm'.
        """
        self._client = DbClient(connection=host,
                                database=database)
        self._collection = SnapshotCollectionClient(self.client, name)

    @property
    def client(self) -> DbClient:
        """Client object."""
        return self._client

    @property
    def collection(self) -> SnapshotCollectionClient:
        """Collection object."""
        return self._collection

    def filter(self,
               data: WaybackMachineResponseCDX) -> WaybackMachineResponseCDX:
        """Filter urls."""

        if self.collection is not None:
            data = data.filter(
                lambda row: self._filter_original(row['original'])
            )
        return data

    def _filter_original(self, original: str) -> bool:
        return len(self.collection.find_original_url(original)) == 0
