"""Wayback Machine CDX spider."""
import abc
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import pandas as pd
import parse
import scrapy

from status.cdx import WaybackMachineCDX

logger = logging.getLogger(__name__)

from_dt = datetime(2020, 12, 15, 0, 0, 0)
to_dt = datetime(2020, 12, 31, 23, 59, 59)


class SpiderWaybackMachineBase(scrapy.Spider, metaclass=abc.ABCMeta):
    """Basic Wayback Machine domain scraper."""

    def __init__(self,
                 cdx: WaybackMachineCDX,
                 *args, **kwargs):

        super().__init__(*args, **kwargs)
        self._cdx = cdx

    def start_requests(self):
        """Starting request."""

        self._cdx.set_output_format('json')
        self._cdx.set_resume_key(show=True)

        request = scrapy.Request(self._cdx.cdx, self.parse_cdx)

        yield request

    def parse_cdx(self, response: scrapy.http.TextResponse):
        """Parse cdx responses."""

        data = WaybackMachineResponseCDX.from_text(response.text)

        data = data.filter(
            lambda row: self.filter_statuscode(row['statuscode']))
        data = data.filter(lambda row: self.filter_url(row['original']))
        data = data.filter(lambda row: self.filter_mimetype(row['mimetype']))

        for url in SnapshotUrlIterator(data):
            yield scrapy.Request(url, self.parse)

        if data.resume_key is not None:

            self._cdx.set_resume_key(show=True, key=data.resume_key)
            request = scrapy.Request(self._cdx.cdx, self.parse_cdx)

            yield request

    @ abc.abstractmethod
    def parse(self, response: scrapy.http.TextResponse):
        """Parse snapshot"""

    def filter_statuscode(self, statuscode: str) -> bool:
        return statuscode != '404'

    def filter_url(self, url: str) -> bool:
        return True

    def filter_mimetype(self, mimetype: str) -> bool:
        return True


class WaybackMachineResponseCDX:
    """CDX response data."""

    url_template = 'https://web.archive.org/web/{timestamp}/{original}'

    def __init__(self, data: pd.DataFrame, resume_key: str):
        """Parse response"""

        self._resume_key = resume_key
        self._data = data

    @ classmethod
    def from_list(cls, data: List[List[str]]) -> 'WaybackMachineResponseCDX':

        if len(data[-2]) == 0:

            resume_key = data[-1][0]
            data = pd.DataFrame(data[1:-2], columns=data[0])

        else:

            resume_key = None
            data = pd.DataFrame(data[1:], columns=data[0])

        return cls(data, resume_key)

    @ classmethod
    def from_text(cls, text) -> 'WaybackMachineResponseCDX':
        """From text json response."""
        json_data = json.loads(text)
        return cls.from_list(json_data)

    @ property
    def resume_key(self) -> Optional[str]:
        """Resume key parsed from response."""
        return self._resume_key

    @ property
    def data(self) -> pd.DataFrame:
        """data."""
        return self._data

    @ property
    def columns(self) -> List[str]:
        """Column names."""
        return self._data.columns

    @ property
    def n_rows(self):
        """Number of rows in the response."""
        return len(self.data.index)

    def filter(self, condition) -> 'WaybackMachineResponseCDX':

        where = self.data.apply(condition, axis=1)
        data_new = self.data[where]

        return WaybackMachineResponseCDX(data_new, resume_key=self.resume_key)

    @classmethod
    def snapshot_to_archive_url(cls, snapshot: Dict[str, str]) -> str:
        """Get archive url."""
        return cls.url_template.format(**snapshot)

    @classmethod
    def to_archive_url(cls, original: str, timestamp: str, **kwargs) -> str:
        """Get archive url."""
        return cls.url_template.format(original=original, timestamp=timestamp)

    @classmethod
    def from_archive_url(cls, archive_url: str) -> Tuple[str, str]:
        """Get archive url."""
        return parse.parse(cls.url_template, archive_url)


class SnapshotUrlIterator:
    """Iterator over snapshot urls."""

    def __init__(self, cdx_data: WaybackMachineResponseCDX):

        self._data = cdx_data
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):

        if self._index < self._data.data.shape[0]:
            row = self._data.data.iloc[self._index]
            snapshot = row.to_dict()

            url = self._data.snapshot_to_archive_url(snapshot)
            self._index += 1
        else:
            raise StopIteration

        return url
