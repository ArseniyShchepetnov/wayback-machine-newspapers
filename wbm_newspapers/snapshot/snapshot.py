"""Snapshot class."""
from typing import Dict, Optional, List
import dataclasses


@dataclasses.dataclass(frozen=True)
class SnapshotData:  # pylint: disable=too-many-instance-attributes
    """Parsed item from article."""

    text: str
    title: str
    publish_date: str
    title_date: str
    url_date: str
    url: str
    path: str
    timestamp: str
    original: str

    @classmethod
    def fields(cls) -> List[str]:
        """Returns list of fields in the data."""
        return [field.name for field in dataclasses.fields(cls)]

    @staticmethod
    def key_fields() -> List[str]:
        """Key fields to distinguish snapshots."""
        fields = ['title', 'publish_date']
        return fields


class Snapshot:
    """Snapshot class."""

    def __init__(self, data: SnapshotData, snapshot: Optional[str] = None):
        """
        Parameters
        ----------
        data : SnapshotData
            _description_
        snapshot : Optional[str], optional
            _description_, by default None
        """
        self._data = data
        self._snapshot = snapshot

    @property
    def data(self) -> SnapshotData:
        """Return data."""
        return self._data

    def equal_pub(self, other: 'Snapshot') -> bool:
        """Checks if publication is equal."""
        result = True
        for key in self.key_fields():
            result = getattr(self.data, key) == getattr(other.data, key)

        return result

    @staticmethod
    def key_fields() -> List[str]:
        """Key fields to distinguish snapshots."""
        return SnapshotData.key_fields()

    def get_keys(self) -> Dict[str, str]:
        """Key fields data."""
        result = {}
        for key in self.key_fields():
            result[key] = getattr(self.data, key)
        return result

    def snapshot_dict(self):
        """Convert to dictionary."""
        data = {'origin': self._snapshot}
        keys = {key: getattr(self.data, key) for key in self.key_fields()}
        data = {**data, **keys}
        return data

    def data_dict(self) -> Dict[str, str]:
        """Convert data to dictionary."""
        data = dataclasses.asdict(self._data)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, str], **kwargs) -> 'Snapshot':
        """Construct snapshot from dictionary with data."""
        snapshot_data = SnapshotData(**data)
        return cls(snapshot_data, **kwargs)
