"""WaybackMachine Response."""
import json
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd
import parse


class WaybackMachineResponseCDX:
    """CDX response data."""

    url_template = 'https://web.archive.org/web/{timestamp}/{original}'

    def __init__(self, data: pd.DataFrame, resume_key: Optional[str] = None):
        """Parse response"""
        self._resume_key = resume_key
        self._data = data

    @classmethod
    def from_list(cls, data: List[List[str]]) -> 'WaybackMachineResponseCDX':
        """Instantiate class form list of lists data."""

        resume_key: Optional[str] = None
        if len(data[-2]) == 0:
            resume_key = data[-1][0]
            data = pd.DataFrame(data[1:-2], columns=data[0])
        else:
            data = pd.DataFrame(data[1:], columns=data[0])

        return cls(data, resume_key)

    @classmethod
    def from_text(cls, text) -> 'WaybackMachineResponseCDX':
        """From text json response."""
        json_data = json.loads(text)
        return cls.from_list(json_data)

    @property
    def resume_key(self) -> Optional[str]:
        """Resume key parsed from response."""
        return self._resume_key

    @property
    def data(self) -> pd.DataFrame:
        """data."""
        return self._data

    @property
    def columns(self) -> List[str]:
        """Column names."""
        return self._data.columns

    @property
    def n_rows(self):
        """Number of rows in the response."""
        return len(self.data.index)

    def filter(self, condition: Callable) -> 'WaybackMachineResponseCDX':
        """Filter by condition."""
        where = self.data.apply(condition, axis=1)
        data_new = self.data[where]
        return WaybackMachineResponseCDX(data_new, resume_key=self.resume_key)

    @classmethod
    def snapshot_to_archive_url(cls, snapshot: Dict[str, str]) -> str:
        """Get archive url."""
        return cls.url_template.format(**snapshot)

    @classmethod
    def to_archive_url(cls, original: str, timestamp: str) -> str:
        """Get archive url."""
        return cls.url_template.format(original=original, timestamp=timestamp)

    @classmethod
    def from_archive_url(cls, archive_url: str) -> Tuple[str, str]:
        """Get archive url."""
        return parse.parse(cls.url_template, archive_url)
